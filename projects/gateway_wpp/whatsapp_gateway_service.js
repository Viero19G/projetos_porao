// whatsapp_gateway_service.js
//Gateway de Wpp
const { Client, LocalAuth, MessageMedia } = require('whatsapp-web.js');
const qrcode = require('qrcode'); // Usaremos a lib qrcode para gerar base64, não qrcode-terminal
const axios = require('axios');
const fs = require('fs').promises;
require('dotenv').config();
const FormData = require('form-data');
const express = require('express');
const http = require('http');
const socketIo = require('socket.io');

const app = express();
const server = http.createServer(app);
const io = socketIo(server, {
    cors: {
        origin: process.env.FRONTEND_URL || "http://localhost:3000", // Permita o acesso do seu frontend Next.js
        methods: ["GET", "POST"]
    }
});

app.use(express.json()); // Para parsear JSON no corpo das requisições

const PORT = process.env.WHATSAPP_GATEWAY_PORT || 3001; // Porta para o seu serviço de gateway

class WhatsAppManager {
    constructor() {
        this.clients = new Map(); // Mapa para armazenar instâncias de clientes WhatsApp por sessionId
        this.qrCodes = new Map(); // Mapa para armazenar QR codes por sessionId
        this.sessionStatus = new Map(); // Mapa para armazenar o status da sessão (conectado, desconectado, QR gerado)
        this.clientConnectedUsers = new Map(); // Mapa para mapear socket.id para user_id DRF

        this.drfApiConfig = {
            baseURL: process.env.DRF_API_BASE_URL || 'http://localhost:8000/api/',
            username: process.env.DRF_USERNAME,
            password: process.env.DRF_PASSWORD,
            jwtToken: null,
            jwtRefreshToken: null,
            jwtFilePath: './jwt.txt',
            jwtRefreshFilePath: './jwt_refresh.txt'
        };

        this.axiosInstance = axios.create({
            baseURL: this.drfApiConfig.baseURL,
            headers: { 'Content-Type': 'application/json' },
            timeout: 60000
        });

        this.setupAuthInterceptors(); // Configura interceptadores de autenticação
    }

    setupAuthInterceptors() {
        this.axiosInstance.interceptors.request.use(
            (config) => {
                if (this.drfApiConfig.jwtToken) {
                    config.headers.Authorization = `Bearer ${this.drfApiConfig.jwtToken}`;
                }
                return config;
            },
            (error) => Promise.reject(error)
        );

        this.axiosInstance.interceptors.response.use(
            (response) => response,
            async (error) => {
                const originalRequest = error.config;
                if (error.response?.status === 401 && !originalRequest._retry) {
                    originalRequest._retry = true;
                    try {
                        const refreshSuccess = await this.refreshJwtToken();
                        if (refreshSuccess) {
                            originalRequest.headers['Authorization'] = `Bearer ${this.drfApiConfig.jwtToken}`;
                            return this.axiosInstance(originalRequest);
                        }
                    } catch (refreshError) {
                        console.error('Erro ao tentar renovar token no interceptor:', refreshError.message);
                    }
                    // Se refresh falhou ou não havia refresh token, tentar login completo
                    const authSuccess = await this.authenticateWithDrfApi();
                    if (authSuccess) {
                        originalRequest.headers['Authorization'] = `Bearer ${this.drfApiConfig.jwtToken}`;
                        return this.axiosInstance(originalRequest);
                    } else {
                        console.error('Falha na reautenticação após 401. Não foi possível continuar.');
                        // Opcional: emitir evento socket para o frontend avisar sobre a necessidade de re-login
                    }
                }
                return Promise.reject(error);
            }
        );
    }

    async authenticateWithDrfApi() {
        try {
            try {
                this.drfApiConfig.jwtToken = (await fs.readFile(this.drfApiConfig.jwtFilePath, 'utf8')).trim();
                this.drfApiConfig.jwtRefreshToken = (await fs.readFile(this.drfApiConfig.jwtRefreshFilePath, 'utf8')).trim();
                console.log('🔑 JWT e Refresh Token lidos do arquivo.');
            } catch (readError) {
                console.warn('⚠️ Arquivo JWT/Refresh Token não encontrado. Iniciando com tokens nulos.');
                this.drfApiConfig.jwtToken = null;
                this.drfApiConfig.jwtRefreshToken = null;
            }

            if (this.drfApiConfig.jwtRefreshToken) {
                const refreshSuccess = await this.refreshJwtToken();
                if (refreshSuccess) return true;
            }

            if (!this.drfApiConfig.jwtToken) {
                if (!this.drfApiConfig.username || !this.drfApiConfig.password) {
                    throw new Error('Credenciais da API DRF não configuradas.');
                }
                console.log('🔄 Obtendo novo JWT (login completo)...');
                const response = await axios.post(`${this.drfApiConfig.baseURL}token/`, {
                    username: this.drfApiConfig.username,
                    password: this.drfApiConfig.password,
                });
                this.drfApiConfig.jwtToken = response.data.access;
                this.drfApiConfig.jwtRefreshToken = response.data.refresh;
                await fs.writeFile(this.drfApiConfig.jwtFilePath, this.drfApiConfig.jwtToken, 'utf8');
                await fs.writeFile(this.drfApiConfig.jwtRefreshFilePath, this.drfApiConfig.jwtRefreshToken, 'utf8');
                console.log('✅ Novo JWT obtido e salvo.');
            }
            return true;
        } catch (error) {
            console.error('❌ Erro ao autenticar com a API DRF:', error.response?.data || error.message);
            this.drfApiConfig.jwtToken = null;
            this.drfApiConfig.jwtRefreshToken = null;
            await fs.unlink(this.drfApiConfig.jwtFilePath).catch(() => {});
            await fs.unlink(this.drfApiConfig.jwtRefreshFilePath).catch(() => {});
            return false;
        }
    }

    async refreshJwtToken() {
        try {
            if (!this.drfApiConfig.jwtRefreshToken) return false;
            console.log('🔄 Tentando renovar Access Token...');
            const response = await axios.post(`${this.drfApiConfig.baseURL}token/refresh/`, {
                refresh: this.drfApiConfig.jwtRefreshToken,
            });
            this.drfApiConfig.jwtToken = response.data.access;
            await fs.writeFile(this.drfApiConfig.jwtFilePath, this.drfApiConfig.jwtToken, 'utf8');
            console.log('✅ Access Token renovado com sucesso.');
            return true;
        } catch (error) {
            console.error('❌ Erro ao renovar JWT:', error.response?.data || error.message);
            this.drfApiConfig.jwtToken = null;
            this.drfApiConfig.jwtRefreshToken = null;
            await fs.unlink(this.drfApiConfig.jwtFilePath).catch(() => {});
            await fs.unlink(this.drfApiConfig.jwtRefreshFilePath).catch(() => {});
            return false;
        }
    }
    
    getNumericWhatsAppId(whatsappIdString) {
        const numericPart = whatsappIdString.replace(/\D/g, ''); 
        try {
            const numericId = parseInt(numericPart, 10);
            if (isNaN(numericId)) {
                console.error(`Falha ao converter ${whatsappIdString} para ID numérico: Resultado NaN.`);
                return null;
            }
            return numericId;
        } catch (e) {
            console.error(`Erro ao converter ${whatsappIdString} para ID numérico:`, e);
            return null;
        }
    }

    async sendToDrfApiAndRespond(originalMessage, messageType, content, mimeType = null) {
        const chat = await originalMessage.getChat();
        let typingInterval;

        try {
            const userIdNumeric = this.getNumericWhatsAppId(originalMessage.from);
            if (userIdNumeric === null) {
                console.error(`❌ Não foi possível obter um ID numérico válido para o usuário: ${originalMessage.from}.`);
                await originalMessage.reply('🔧 Desculpe, não consegui identificar seu ID de usuário. Por favor, tente novamente.');
                return;
            }

            await chat.sendStateTyping();
            typingInterval = setInterval(async () => {
                try {
                    await chat.sendStateTyping();
                } catch (error) {
                    console.log('Erro ao renovar estado de digitação:', error.message);
                }
            }, 2000);

            let axiosConfig = {
                method: 'post',
                url: 'message/',
                data: {},
                headers: { 'Content-Type': 'application/json' }
            };

            if (messageType === 'text') {
                axiosConfig.data = { type: 'text', content: content, user_id: userIdNumeric };
            } else if (messageType === 'command') {
                axiosConfig.data = { type: 'command', command: content.command, user_id: userIdNumeric };
            } else if (messageType === 'audio') {
                const formData = new FormData();
                formData.append('type', 'audio');
                const audioBuffer = Buffer.from(content, 'base64');
                
                formData.append('audio_file', audioBuffer, {
                    filename: 'audio.ogg', 
                    contentType: mimeType 
                });
                formData.append('user_id', userIdNumeric);

                axiosConfig.data = formData;
                axiosConfig.headers = { ...formData.getHeaders() }; 
            } else {
                throw new Error(`Tipo de mensagem '${messageType}' não suportado para envio à API.`);
            }

            const response = await this.axiosInstance(axiosConfig); // Usar a instância Axios com interceptores
            const contentType = response.headers['content-type'];
            console.log('Content-Type da resposta da API DRF:', contentType);

            if (contentType && contentType.includes('application/json')) {
                const apiResponse = response.data; 
                
                if (apiResponse.status === 'success') {
                    switch (apiResponse.type) {
                        case 'text':
                        case 'command_response':
                            await originalMessage.reply(apiResponse.response);
                            break;
                        case 'audio':
                            if (apiResponse.response && apiResponse.mime_type) {
                                let audioBase64 = apiResponse.response;
                                const mimeType = apiResponse.mime_type;
                                
                                if (audioBase64) {
                                    audioBase64 = audioBase64.replace(/[\n\r]/g, '');
                                }

                                try {
                                    const media = new MessageMedia(mimeType, audioBase64, 'resposta_ia.ogg');
                                    await originalMessage.reply(media);
                                    console.log('DEBUG: Áudio de resposta enviado com sucesso para o WhatsApp!');
                                } catch (mediaError) {
                                    console.error('❌ Erro ao criar ou enviar MessageMedia:', mediaError);
                                    await originalMessage.reply('Desculpe, não consegui enviar o áudio de resposta. Erro interno ao processar mídia.');
                                }
                            } else {
                                console.warn('JSON de áudio de sucesso sem base64 ou mime_type:', apiResponse);
                                await originalMessage.reply('Recebi um áudio, mas não consegui reproduzi-lo.');
                            }
                            break;
                        case 'image':
                        case 'video':
                        case 'document':
                            if (apiResponse.response && apiResponse.mime_type) {
                                const media = new MessageMedia(apiResponse.mime_type, apiResponse.response, 'response_media');
                                await originalMessage.reply(media);
                            } else {
                                console.warn(`JSON de ${apiResponse.type} sem base64/URL ou mime_type:`, apiResponse);
                                await originalMessage.reply(`Recebi um(a) ${apiResponse.type}, mas não consegui exibi-lo(a).`);
                            }
                            break;
                        default:
                            console.warn('Tipo de resposta JSON de sucesso inesperado:', apiResponse.type);
                            await originalMessage.reply('Recebi uma resposta do servidor, mas não sei como processá-la.');
                            break;
                    }
                } else {
                    console.error('❌ Erro detalhado da API (JSON):', apiResponse.message || apiResponse.detail || JSON.stringify(apiResponse));
                    await originalMessage.reply(`Erro da API: ${apiResponse.message || apiResponse.detail || 'Ocorreu um erro desconhecido.'}`);
                }
            } else {
                console.warn('⚠️ Resposta da API com Content-Type inesperado ou sem JSON:', contentType);
                if (response.data) {
                    try {
                        console.warn('Conteúdo bruto da resposta (primeiros 500 chars):', Buffer.from(response.data).toString('utf8').substring(0, 500));
                    } catch (e) {
                        console.warn('Não foi possível converter resposta para string para log (não é texto):', e.message);
                    }
                }
                await originalMessage.reply('Desculpe, recebi uma resposta do servidor que não consigo entender.');
            }

        } catch (error) {
            console.error('❌ Erro na comunicação com a API DRF ou reautenticação:', error.message);
            await originalMessage.reply('🔧 Desculpe, ocorreu um erro ao comunicar com o servidor. Tente novamente.');
        } finally {
            if (typingInterval) {
                clearInterval(typingInterval);
            }
            await chat.clearState();
        }
    }


    async initializeClient(sessionId, userId, connectionName, agentName, agentPrompt, socket) {
        if (this.clients.has(sessionId)) {
            socket.emit('whatsapp-status', { sessionId, status: 'already_initialized', message: 'Sessão já inicializada.' });
            return;
        }

        console.log(`🚀 Iniciando cliente WhatsApp para sessão: ${sessionId} (User ID: ${userId})`);
        
        const client = new Client({
            authStrategy: new LocalAuth({ clientId: `whatsapp-bot-${sessionId}` }),
            puppeteer: {
                headless: true,
                args: ['--no-sandbox', '--disable-setuid-sandbox']
            }
        });

        this.clients.set(sessionId, client);
        this.sessionStatus.set(sessionId, 'initializing');
        this.clientConnectedUsers.set(socket.id, userId); // Armazena o mapeamento

        client.on('qr', async (qr) => {
            console.log(`QR_CODE gerado para sessão ${sessionId}`);
            const qrBase64 = await qrcode.toDataURL(qr);
            this.qrCodes.set(sessionId, qrBase64);
            this.sessionStatus.set(sessionId, 'qr_generated');
            socket.emit('qr-code', { sessionId, qr: qrBase64 });
        });

        client.on('ready', async () => {
            console.log(`✅ Cliente WhatsApp para sessão ${sessionId} está pronto!`);
            this.sessionStatus.set(sessionId, 'connected');
            this.qrCodes.delete(sessionId); // Limpa o QR code após conexão
            socket.emit('whatsapp-status', { sessionId, status: 'connected', message: 'Conectado com sucesso!' });

            // **ENVIAR INFORMAÇÕES DA NOVA CONEXÃO PARA SUA API DRF AQUI**
            // Você precisa adaptar o endpoint e os dados conforme sua API DRF espera.
            try {
                const payload = {
                    session_id: sessionId,
                    user_id: userId, // ID do usuário que iniciou a conexão
                    name: connectionName,
                    agent_name: agentName,
                    agent_prompt: agentPrompt,
                    phone_number: client.info.me.user // Salvar o número de telefone conectado
                };
                console.log("Enviando nova conexão para DRF:", payload);
                // Certifique-se que o endpoint '/whatsapp/connections/create/' existe na sua DRF
                const response = await this.axiosInstance.post('/whatsapp/connections/create/', payload);
                console.log('Informações da nova conexão salvas na DRF:', response.data);
            } catch (drfError) {
                console.error(`❌ Erro ao salvar informações da conexão ${sessionId} na DRF:`, drfError.response?.data || drfError.message);
                socket.emit('whatsapp-status', { sessionId, status: 'error', message: `Erro ao salvar na DRF: ${drfError.response?.data?.detail || drfError.message}` });
            }
        });

        client.on('auth_failure', (msg) => {
            console.error(`❌ Falha na autenticação da sessão ${sessionId}:`, msg);
            this.sessionStatus.set(sessionId, 'auth_failure');
            socket.emit('whatsapp-status', { sessionId, status: 'auth_failure', message: msg });
        });

        client.on('disconnected', (reason) => {
            console.log(`❌ Cliente da sessão ${sessionId} desconectado:`, reason);
            this.sessionStatus.set(sessionId, 'disconnected');
            this.clients.delete(sessionId); // Remove a instância desconectada
            this.qrCodes.delete(sessionId);
            socket.emit('whatsapp-status', { sessionId, status: 'disconnected', message: reason });
            // Notificar DRF sobre desconexão, se houver um endpoint para isso
            this.notifyDrfDisconnect(sessionId);
        });

        client.on('message', async (message) => {
            await this.handleMessage(message);
        });

        client.on('message_create', async (message) => {
            if (message.hasMedia && message.type === 'ptt' && !message.fromMe) {
                console.log(`🎤 Mensagem de áudio recebida de ${message.from} para sessão ${sessionId}`);
                await this.handleMediaMessage(message);
            }
        });

        client.initialize().catch(err => {
            console.error(`Erro ao inicializar sessão ${sessionId}:`, err);
            this.sessionStatus.set(sessionId, 'error');
            socket.emit('whatsapp-status', { sessionId, status: 'error', message: `Erro na inicialização: ${err.message}` });
        });
    }

    async disconnectClient(sessionId) {
        const client = this.clients.get(sessionId);
        if (client) {
            console.log(`🛑 Desconectando sessão: ${sessionId}`);
            await client.destroy(); // Isso irá disparar o evento 'disconnected'
            // O evento 'disconnected' já limpa os mapas
            await this.notifyDrfDisconnect(sessionId);
            return true;
        }
        return false;
    }

    async notifyDrfDisconnect(sessionId) {
        try {
            console.log(`Notificando DRF sobre desconexão da sessão ${sessionId}`);
            // Seu endpoint DRF para desconexão deve ser capaz de remover ou marcar a sessão como inativa
            // Ex: POST /whatsapp/disconnect/<session_id>/
            await this.axiosInstance.post(`/whatsapp/disconnect/${sessionId}/`, { session_id: sessionId });
            console.log(`DRF notificada sobre desconexão da sessão ${sessionId}`);
        } catch (error) {
            console.error(`❌ Erro ao notificar DRF sobre desconexão da sessão ${sessionId}:`, error.response?.data || error.message);
        }
    }

    getSessionInfo(sessionId) {
        return {
            sessionId: sessionId,
            status: this.sessionStatus.get(sessionId) || 'unknown',
            qrCode: this.qrCodes.get(sessionId) || null // O QR code só estará aqui se o status for 'qr_generated'
        };
    }

    getAllSessionsInfo() {
        const sessions = [];
        for (const [sessionId, status] of this.sessionStatus.entries()) {
            sessions.push({
                sessionId: sessionId,
                status: status,
                qrCode: this.qrCodes.get(sessionId) || null
            });
        }
        return sessions;
    }
}

const whatsappManager = new WhatsAppManager();

// --- Rotas de API para o frontend ---

// Endpoint para verificar o status do gateway e autenticação DRF
app.get('/status', async (req, res) => {
    const authSuccess = await whatsappManager.authenticateWithDrfApi();
    res.json({
        gateway_status: 'online',
        drf_auth_status: authSuccess ? 'authenticated' : 'failed',
        drf_api_base_url: whatsappManager.drfApiConfig.baseURL
    });
});

// Endpoint para iniciar uma nova sessão (o frontend chama isso)
app.post('/start-session', async (req, res) => {
    const { sessionId, userId, connectionName, agentName, agentPrompt } = req.body;
    if (!sessionId || !userId || !connectionName || !agentName || !agentPrompt) {
        return res.status(400).json({ error: 'Dados incompletos para iniciar a sessão.' });
    }

    // Assumimos que o userId vem de um usuário autenticado no frontend
    // E que o frontend passará um sessionId único (UUID por exemplo)
    
    // O socket.id será necessário para emitir o QR Code para o cliente correto
    // Portanto, essa lógica precisa ser refatorada para ser chamada via Socket.IO
    // Ou o frontend faz uma chamada REST e depois escuta um evento Socket.IO
    // Vamos usar a abordagem Socket.IO para a comunicação em tempo real do QR
    res.status(202).json({ message: 'Processo de sessão iniciado. Aguarde o QR Code via WebSocket.' });
});

// Endpoint para desconectar uma sessão (o frontend chama isso)
app.post('/disconnect-session', async (req, res) => {
    const { sessionId } = req.body;
    if (!sessionId) {
        return res.status(400).json({ error: 'ID da sessão é necessário para desconectar.' });
    }
    const success = await whatsappManager.disconnectClient(sessionId);
    if (success) {
        res.json({ message: `Sessão ${sessionId} desconectada com sucesso.` });
    } else {
        res.status(404).json({ error: `Sessão ${sessionId} não encontrada ou já desconectada.` });
    }
});

// Endpoint para listar as sessões (pode ser útil para depuração ou administração)
app.get('/sessions', (req, res) => {
    res.json(whatsappManager.getAllSessionsInfo());
});

// --- Configuração do Socket.IO ---
io.on('connection', (socket) => {
    console.log('Cliente Socket.IO conectado:', socket.id);

    socket.on('start-whatsapp-session', async (data) => {
        const { sessionId, userId, connectionName, agentName, agentPrompt } = data;
        if (!sessionId || !userId || !connectionName || !agentName || !agentPrompt) {
            socket.emit('whatsapp-status', { sessionId, status: 'error', message: 'Dados incompletos para iniciar a sessão.' });
            return;
        }
        console.log(`Recebida requisição para iniciar sessão ${sessionId} para User ID: ${userId}`);
        await whatsappManager.initializeClient(sessionId, userId, connectionName, agentName, agentPrompt, socket);
    });

    socket.on('disconnect', () => {
        console.log('Cliente Socket.IO desconectado:', socket.id);
        // Opcional: Lidar com a desconexão do socket se isso impactar as sessões do WhatsApp
        // Por exemplo, se o usuário do frontend fechar a aba, você pode querer desconectar as sessões
        // associadas a ele, mas isso depende da sua lógica de negócio (se as sessões devem persistir)
    });
});

// Inicia o servidor Express e Socket.IO
server.listen(PORT, async () => {
    console.log(`🚀 Gateway WhatsApp rodando na porta ${PORT}`);
    console.log(`🔗 API DRF Base URL: ${whatsappManager.drfApiConfig.baseURL}`);

    // Tentar autenticar com DRF ao iniciar o gateway
    const authSuccess = await whatsappManager.authenticateWithDrfApi();
    if (!authSuccess) {
        console.error('❌ Não foi possível autenticar o Gateway com a API DRF no início.');
    }
});

// Gerenciamento de sinais de interrupção para desligamento gracioso
process.on('SIGINT', async () => {
    console.log('\n🛑 Recebido sinal de interrupção...');
    // Desconectar todos os clientes WhatsApp antes de sair
    for (const client of whatsappManager.clients.values()) {
        await client.destroy().catch(e => console.error('Erro ao destruir cliente na saída:', e));
    }
    process.exit(0);
});

process.on('SIGTERM', async () => {
    console.log('\n🛑 Recebido sinal de terminação...');
    for (const client of whatsappManager.clients.values()) {
        await client.destroy().catch(e => console.error('Erro ao destruir cliente na saída:', e));
    }
    process.exit(0);
});