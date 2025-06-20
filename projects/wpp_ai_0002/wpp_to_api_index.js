// wpp_to_api_index.js

const { Client, LocalAuth, MessageMedia } = require('whatsapp-web.js');
const qrcode = require('qrcode-terminal');
const axios = require('axios');
const fs = require('fs').promises; // Para operações assíncronas com arquivos
require('dotenv').config(); // Carrega as variáveis de ambiente do arquivo .env

// Polifills para FormData em Node.js.
// Certifique-se de que 'form-data' está instalado (npm install form-data)
const FormData = require('form-data');
// Remove a declaração global.Blob, pois enviaremos o Buffer diretamente
// try {
//     global.Blob = require('node:buffer').Blob; // Node.js 16+
// } catch (e) {
//     console.warn("node:buffer.Blob not available. If you encounter issues with FormData and Blob, consider adding 'node-fetch' or similar polyfill.");
// }

class WhatsAppOpenAIBot {
    constructor() {
        // Configuração do cliente WhatsApp Web
        this.client = new Client({
            authStrategy: new LocalAuth({ clientId: "whatsapp-bot-jwt" }), // Garante sessão local única
            puppeteer: {
                headless: true, // Modo headless (sem interface gráfica)
                args: ['--no-sandbox', '--disable-setuid-sandbox'] // Argumentos para compatibilidade em diferentes ambientes
            }
        });

        // Configurações da API DRF
        this.drfApiConfig = {
            baseURL: process.env.DRF_API_BASE_URL || 'http://localhost:8000/api/',
            username: process.env.DRF_USERNAME,
            password: process.env.DRF_PASSWORD,
            jwtToken: null, // Token de acesso JWT (access token)
            jwtRefreshToken: null, // Token de renovação JWT (refresh token)
            jwtFilePath: './jwt.txt', // Caminho para armazenar o access token
            jwtRefreshFilePath: './jwt_refresh.txt' // Caminho para armazenar o refresh token
        };

        // Configuração inicial para Axios para evitar redefinições
        this.axiosInstance = axios.create({
            baseURL: this.drfApiConfig.baseURL,
            headers: {
                'Content-Type': 'application/json',
            },
            timeout: 60000 // Aumenta o timeout para 60 segundos (1 minuto) para esperar a API
        });

        this.setupEventListeners();
    }

    /**
     * Configura os listeners de eventos do cliente WhatsApp.
     */
    setupEventListeners() {
        this.client.on('qr', (qr) => {
            console.log('Escaneie o QR Code abaixo com seu WhatsApp:');
            qrcode.generate(qr, { small: true });
        });

        this.client.on('ready', async () => {
            console.log('✅ WhatsApp Bot está pronto!');
            await this.authenticateWithDrfApi(); // Tenta autenticar com a API DRF ao iniciar
        });

        this.client.on('message', async (message) => {
            await this.handleMessage(message);
        });

        this.client.on('message_create', async (message) => {
            // Processa mensagens de áudio (PTT - Push To Talk) que não são enviadas pelo próprio bot
            if (message.hasMedia && message.type === 'ptt' && !message.fromMe) {
                console.log(`🎤 Mensagem de áudio recebida de ${message.from}`);
                await this.handleMediaMessage(message);
            }
        });

        this.client.on('auth_failure', (msg) => {
            console.error('❌ Falha na autenticação do WhatsApp:', msg);
        });

        this.client.on('disconnected', (reason) => {
            console.log('❌ Cliente desconectado do WhatsApp:', reason);
        });
    }

    // --- Métodos de Autenticação JWT com a API DRF ---

    /**
     * Tenta autenticar com a API DRF. Primeiro tenta renovar o token existente,
     * se falhar, tenta fazer um novo login completo.
     * @returns {boolean} True se a autenticação foi bem-sucedida, False caso contrário.
     */
    async authenticateWithDrfApi() {
        try {
            // 1. Tentar ler o Access Token e Refresh Token do arquivo
            try {
                this.drfApiConfig.jwtToken = (await fs.readFile(this.drfApiConfig.jwtFilePath, 'utf8')).trim();
                this.drfApiConfig.jwtRefreshToken = (await fs.readFile(this.drfApiConfig.jwtRefreshFilePath, 'utf8')).trim();
                console.log('🔑 JWT e Refresh Token lidos do arquivo. Tentando usar...');
            } catch (readError) {
                console.warn('⚠️ Arquivo JWT/Refresh Token não encontrado ou erro de leitura. Iniciando com tokens nulos.');
                this.drfApiConfig.jwtToken = null;
                this.drfApiConfig.jwtRefreshToken = null;
            }

            // 2. Se houver Refresh Token, tentar renovar
            if (this.drfApiConfig.jwtRefreshToken) {
                const refreshSuccess = await this.refreshJwtToken();
                if (refreshSuccess) {
                    return true; // Access token renovado, podemos prosseguir
                }
            }

            // 3. Se ainda não tiver Access Token (ou o refresh falhou), fazer login completo
            if (!this.drfApiConfig.jwtToken) {
                if (!this.drfApiConfig.username || !this.drfApiConfig.password) {
                    throw new Error('Credenciais de usuário e senha da API DRF não configuradas no .env para login.');
                }
                console.log('🔄 Obtendo novo JWT (login completo) da API DRF...');
                const loginUrl = 'token/'; // Endpoint correto: /api/token/
                const response = await this.axiosInstance.post(loginUrl, {
                    username: this.drfApiConfig.username,
                    password: this.drfApiConfig.password,
                });

                this.drfApiConfig.jwtToken = response.data.access;
                this.drfApiConfig.jwtRefreshToken = response.data.refresh; // Salva o refresh token

                await fs.writeFile(this.drfApiConfig.jwtFilePath, this.drfApiConfig.jwtToken, 'utf8');
                await fs.writeFile(this.drfApiConfig.jwtRefreshFilePath, this.drfApiConfig.jwtRefreshToken, 'utf8');
                console.log('✅ Novo JWT obtido e salvo com sucesso.');
            }
            return true;
        } catch (error) {
            console.error('❌ Erro ao autenticar com a API DRF:', error.response?.data || error.message);
            // Limpa tokens em caso de falha para forçar novo login na próxima tentativa
            this.drfApiConfig.jwtToken = null;
            this.drfApiConfig.jwtRefreshToken = null;
            await fs.unlink(this.drfApiConfig.jwtFilePath).catch(() => {});
            await fs.unlink(this.drfApiConfig.jwtRefreshFilePath).catch(() => {});
            return false;
        }
    }

    /**
     * Tenta renovar o Access Token usando o Refresh Token existente.
     * @returns {boolean} True se a renovação foi bem-sucedida, False caso contrário.
     */
    async refreshJwtToken() {
        try {
            if (!this.drfApiConfig.jwtRefreshToken) {
                console.warn('⚠️ Não há Refresh Token disponível para renovação.');
                return false;
            }

            console.log('🔄 Tentando renovar Access Token usando Refresh Token...');
            const refreshUrl = 'token/refresh/'; // Endpoint correto: /api/token/refresh/
            const response = await this.axiosInstance.post(refreshUrl, {
                refresh: this.drfApiConfig.jwtRefreshToken,
            });

            this.drfApiConfig.jwtToken = response.data.access; // Novo access token
            // Se o refresh token também for atualizado pela API (opcional na sua configuração JWT),
            // você pode salvá-lo novamente aqui:
            // this.drfApiConfig.jwtRefreshToken = response.data.refresh;
            
            await fs.writeFile(this.drfApiConfig.jwtFilePath, this.drfApiConfig.jwtToken, 'utf8');
            // await fs.writeFile(this.drfApiConfig.jwtRefreshFilePath, this.drfApiConfig.jwtRefreshToken, 'utf8');
            console.log('✅ Access Token renovado com sucesso.');
            return true;
        } catch (error) {
            console.error('❌ Erro ao renovar JWT usando Refresh Token:', error.response?.data || error.message);
            // Invalida ambos os tokens se o refresh falhar (refresh token expirado/inválido)
            this.drfApiConfig.jwtToken = null;
            this.drfApiConfig.jwtRefreshToken = null;
            await fs.unlink(this.drfApiConfig.jwtFilePath).catch(() => {});
            await fs.unlink(this.drfApiConfig.jwtRefreshFilePath).catch(() => {});
            return false;
        }
    }

    /**
     * Garante que a chamada à API é feita com um token autenticado.
     * Tenta reautenticar se receber um 401.
     * @param {object} axiosConfig - Configuração do Axios para a requisição.
     * @returns {Promise<object>} A resposta da requisição Axios.
     * @throws {Error} Se a autenticação falhar completamente ou ocorrer outro erro.
     */
    async ensureAuthenticatedCall(axiosConfig) {
        let response;
        try {
            // Adiciona o token de autorização à requisição
            axiosConfig.headers = {
                ...axiosConfig.headers,
                'Authorization': `Bearer ${this.drfApiConfig.jwtToken}`,
            };
            response = await this.axiosInstance(axiosConfig); // Usa a instância Axios configurada
            return response;
        } catch (error) {
            if (error.response && error.response.status === 401) {
                console.warn('Token JWT expirado ou inválido. Tentando reautenticar...');
                const authSuccess = await this.authenticateWithDrfApi(); // Tentar reautenticar (inclui refresh ou login)
                if (authSuccess) {
                    // Se a reautenticação for bem-sucedida, tenta a requisição original novamente com o novo token
                    axiosConfig.headers['Authorization'] = `Bearer ${this.drfApiConfig.jwtToken}`;
                    response = await this.axiosInstance(axiosConfig);
                    return response;
                } else {
                    throw new Error('Falha total na autenticação com a API DRF. Não foi possível continuar.');
                }
            } else {
                throw error; // Lança outros erros (rede, 404, 500, etc.)
            }
        }
    }

    // --- Métodos de Tratamento de Mensagens do WhatsApp ---

    /**
     * Extrai apenas os dígitos do ID do WhatsApp e tenta convertê-los para um inteiro.
     * Retorna null se a conversão falhar.
     * @param {string} whatsappIdString - O ID do WhatsApp no formato "555491602127@c.us".
     * @returns {number|null} O ID numérico ou null.
     */
    getNumericWhatsAppId(whatsappIdString) {
        // Remove tudo que não for dígito
        const numericPart = whatsappIdString.replace(/\D/g, ''); 
        
        try {
            // Tenta converter para inteiro
            const numericId = parseInt(numericPart, 10);
            // Verifica se a conversão resultou em um número válido
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

    /**
     * Lida com mensagens de texto e comandos recebidos do WhatsApp.
     * @param {object} message - Objeto de mensagem do whatsapp-web.js.
     */
    async handleMessage(message) {
        try {
            // Ignora mensagens de status, mensagens enviadas pelo próprio bot ou com mídia (lidado por message_create)
            if (message.from === 'status@broadcast' || message.fromMe || message.hasMedia) {
                return;
            }

            if (message.type === 'chat') {
                console.log(`📨 Mensagem de texto recebida de ${message.from}: ${message.body}`);
            }

            // Lógica para comandos específicos
            if (message.body.toLowerCase().startsWith('/limpar')) {
                await this.sendToDrfApiAndRespond(message, 'command', { command: 'clear_history' });
                return;
            }

            if (message.body.toLowerCase().startsWith('/ajuda')) {
                const helpText = `🤖 *Comandos disponíveis:*
                
/limpar - Limpa o histórico da conversa com a IA.
/ajuda - Mostra esta mensagem de ajuda.

Basta enviar uma mensagem de texto ou áudio e eu responderei usando IA!`;
                await message.reply(helpText);
                return;
            }

            // Se for uma mensagem de texto normal, envia para a API DRF
            if (message.type === 'chat') {
                await this.sendToDrfApiAndRespond(message, 'text', message.body);
            } else {
                await message.reply('Desculpe, no momento só consigo processar mensagens de texto ou áudio.');
            }

        } catch (error) {
            console.error('❌ Erro ao processar mensagem:', error);
            await message.reply('🔧 Desculpe, ocorreu um erro ao processar sua mensagem. Tente novamente.');
        }
    }

    /**
     * Lida com mensagens de mídia (especificamente PTT/áudio) recebidas do WhatsApp.
     * @param {object} message - Objeto de mensagem do whatsapp-web.js.
     */
    async handleMediaMessage(message) {
        try {
            if (message.type === 'ptt') {
                console.log(`Audio recebido. Baixando...`);
                const media = await message.downloadMedia();
                await this.sendToDrfApiAndRespond(message, 'audio', media.data, media.mimetype);
            } else {
                console.log(`Mídia do tipo ${message.type} recebida, mas não processada.`);
                await message.reply('Recebi sua mídia, mas no momento só consigo processar áudios.');
            }
        } catch (error) {
            console.error('❌ Erro ao lidar com mensagem de mídia:', error);
            await message.reply('🔧 Desculpe, ocorreu um erro ao processar sua mensagem de áudio. Tente novamente.');
        }
    }

    /**
     * Envia a mensagem para a API DRF e processa a resposta.
     * @param {object} originalMessage - O objeto da mensagem original do WhatsApp.
     * @param {string} messageType - O tipo de mensagem ('text', 'audio', 'command').
     * @param {any} content - O conteúdo da mensagem (texto, base64 do áudio, objeto de comando).
     * @param {string} [mimeType=null] - O tipo MIME do conteúdo (para áudio).
     */
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
                data: {}, // Inicializa data como um objeto vazio
                headers: { 'Content-Type': 'application/json' } // Default para JSON
            };

            // Preenche os dados e headers com base no tipo de mensagem
            if (messageType === 'text') {
                axiosConfig.data = { type: 'text', content: content, user_id: userIdNumeric };
            } else if (messageType === 'command') {
                axiosConfig.data = { type: 'command', command: content.command, user_id: userIdNumeric };
            } else if (messageType === 'audio') {
                const formData = new FormData();
                formData.append('type', 'audio');
                const audioBuffer = Buffer.from(content, 'base64');
                // Alteração aqui: Passa o Buffer diretamente.
                // O terceiro argumento é o nome do arquivo, que pode ser útil para a API.
                formData.append('audio_file', audioBuffer, {
                    filename: 'audio.ogg', // Nome do arquivo que a API receberá
                    contentType: mimeType // Tipo MIME do arquivo
                });
                formData.append('user_id', userIdNumeric);

                axiosConfig.data = formData;
                axiosConfig.headers = { ...formData.getHeaders() }; // Headers para multipart/form-data
                // É essencial que a API retorne JSON para a resposta, não binário diretamente,
                // a menos que você queira tratar isso separadamente no frontend com responseType: 'arraybuffer' aqui.
                // Para este caso, a API deve retornar JSON contendo o base64 do áudio se for uma resposta de áudio.
            } else {
                throw new Error(`Tipo de mensagem '${messageType}' não suportado para envio à API.`);
            }

            const response = await this.ensureAuthenticatedCall(axiosConfig);
            const contentType = response.headers['content-type'];
            console.log('Content-Type da resposta da API DRF:', contentType);

            // --- Lógica de tratamento de resposta dinâmica SIMPLIFICADA ---
            if (contentType && contentType.includes('application/json')) {
                const apiResponse = response.data; // Axios já parseia JSON automaticamente por padrão

                if (apiResponse.status === 'success') {
                    switch (apiResponse.type) {
                        case 'text':
                        case 'command_response':
                            await originalMessage.reply(apiResponse.response);
                            break;
                        case 'audio':
                            if (apiResponse.response && apiResponse.mime_type) {
                                // Assume que o 'response' do JSON contém o base64 do áudio
                                const media = new MessageMedia(apiResponse.mime_type, apiResponse.response, 'response');
                                await originalMessage.reply(media);
                            } else {
                                console.warn('JSON de áudio de sucesso sem base64 ou mime_type:', apiResponse);
                                await originalMessage.reply('Recebi um áudio, mas não consegui reproduzi-lo.');
                            }
                            break;
                        case 'image':
                        case 'video':
                        case 'document':
                            if (apiResponse.response && apiResponse.mime_type) {
                                // Para outros tipos de mídia (se o Django retornar base64/URL e mimetype)
                                const media = new MessageMedia(apiResponse.mime_type, apiResponse.response, 'response');
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
                    // Caso a API retorne um JSON de erro (com status: 'error' ou similar)
                    console.error('Erro detalhado da API (JSON):', apiResponse.message || apiResponse.detail || JSON.stringify(apiResponse));
                    await originalMessage.reply(`Erro da API: ${apiResponse.message || apiResponse.detail || 'Ocorreu um erro desconhecido.'}`);
                }
            } else {
                // Caso a API retorne um Content-Type desconhecido ou não suportado diretamente
                // Ex: Se a API retornar um áudio binário *diretamente* sem JSON.
                // O Axios geralmente não parseia isso automaticamente, mas `response.data` conterá o binário.
                console.warn('Resposta da API com Content-Type inesperado ou sem JSON:', contentType);
                // Tentar logar o conteúdo bruto para depuração
                if (response.data) {
                    try {
                        console.warn('Conteúdo bruto da resposta:', Buffer.from(response.data).toString('utf8').substring(0, 500) + '...'); // Limita o log
                    } catch (e) {
                        console.warn('Não foi possível converter resposta para string para log:', e.message);
                    }
                }
                await originalMessage.reply('Desculpe, recebi uma resposta do servidor que não consigo entender.');
            }
            // --- Fim da lógica de tratamento de resposta dinâmica ---

        } catch (error) {
            // Captura erros de rede, erros da API que não foram 401 e erros de reautenticação
            console.error('❌ Erro na comunicação com a API DRF ou reautenticação:', error.message);
            // Mensagem amigável para o usuário
            await originalMessage.reply('🔧 Desculpe, ocorreu um erro ao comunicar com o servidor. Tente novamente.');
        } finally {
            // Garante que o estado de "digitando" é limpo
            if (typingInterval) {
                clearInterval(typingInterval);
            }
            await chat.clearState();
        }
    }

    /**
     * Inicia o cliente WhatsApp e as dependências.
     */
    async start() {
        console.log('🚀 Iniciando WhatsApp Bot (Gateway para DRF com JWT)...');
        
        // Valida as variáveis de ambiente essenciais
        if (!this.drfApiConfig.baseURL || !this.drfApiConfig.username || !this.drfApiConfig.password) {
            console.error('❌ DRF_API_BASE_URL, DRF_USERNAME ou DRF_PASSWORD não estão configurados no arquivo .env');
            process.exit(1); // Encerra o processo se as configs essenciais estiverem faltando
        }

        console.log(`🔗 Bot configurado para conectar em: ${this.drfApiConfig.baseURL}`);

        await this.client.initialize();
    }

    /**
     * Para o cliente WhatsApp.
     */
    async stop() {
        console.log('🛑 Parando WhatsApp Bot...');
        await this.client.destroy();
    }
}

// Inicializa e executa o bot
const bot = new WhatsAppOpenAIBot();

// Gerenciamento de sinais de interrupção para desligamento gracioso
process.on('SIGINT', async () => {
    console.log('\n🛑 Recebido sinal de interrupção...');
    await bot.stop();
    process.exit(0);
});

process.on('SIGTERM', async () => {
    console.log('\n🛑 Recebido sinal de terminação...');
    await bot.stop();
    process.exit(0);
});

// Inicia o bot, capturando e logando quaisquer erros fatais
bot.start().catch(error => {
    console.error('❌ Erro fatal ao iniciar o bot:', error);
    process.exit(1);
});

module.exports = WhatsAppOpenAIBot;