const { Client, LocalAuth } = require('whatsapp-web.js');
const qrcode = require('qrcode-terminal');
const axios = require('axios');
require('dotenv').config();

class WhatsAppOpenAIBot {
    constructor() {
        // Inicializar cliente WhatsApp
        this.client = new Client({
            authStrategy: new LocalAuth(),
            puppeteer: {
                headless: true,
                args: ['--no-sandbox', '--disable-setuid-sandbox']
            }
        });

        // Configuração da OpenAI
        this.openaiConfig = {
            apiKey: process.env.OPENAI_API_KEY,
            baseURL: 'https://api.openai.com/v1',
            model: 'gpt-4o-mini', // Modelo mais econômico
            maxTokens: process.env.MAX_TOKENS, // Limita a ~50 palavras (1 token ≈ 0.75 palavras em português)
            temperature: process.env.TEMPERATURE, // Menos criativo, mais direto
            maxHistoryTurns: process.env.MAX_HISTORY // Máximo de 3 perguntas + 3 respostas no histórico
        };

        // Histórico de conversas por usuário (armazenamento em memória)
        this.conversationHistory = new Map();

        this.setupEventListeners();
    }

    setupEventListeners() {
        // Evento para mostrar QR Code
        this.client.on('qr', (qr) => {
            console.log('Escaneie o QR Code abaixo com seu WhatsApp:');
            qrcode.generate(qr, { small: true });
        });

        // Evento quando o cliente está pronto
        this.client.on('ready', () => {
            console.log('✅ WhatsApp Bot está pronto!');
        });

        // Evento para mensagens recebidas
        this.client.on('message', async (message) => {
            await this.handleMessage(message);
        });

        // Evento para erros
        this.client.on('auth_failure', (msg) => {
            console.error('❌ Falha na autenticação:', msg);
        });

        this.client.on('disconnected', (reason) => {
            console.log('❌ Cliente desconectado:', reason);
        });
    }

    async handleMessage(message) {
        try {
            // Verificar se é uma mensagem de texto e não é do próprio bot
            if (message.type !== 'chat' || message.from === 'status@broadcast') {
                return;
            }

            // Ignorar mensagens enviadas pelo próprio bot
            if (message.fromMe) {
                return;
            }

            console.log(`📨 Mensagem recebida de ${message.from}: ${message.body}`);

            // Verificar se é um comando especial
            if (message.body.toLowerCase().startsWith('/limpar')) {
                this.conversationHistory.delete(message.from);
                await message.reply('🧹 Histórico de conversa limpo!');
                return;
            }

            if (message.body.toLowerCase().startsWith('/ajuda')) {
                const helpText = `🤖 *Comandos disponíveis:*
                
                /limpar - Limpa o histórico da conversa
                /ajuda - Mostra esta mensagem de ajuda

                Simplesmente envie uma mensagem de texto e eu responderei usando IA!`;
                await message.reply(helpText);
                return;
            }

            // Obter o chat para mostrar indicador de digitação
            const chat = await message.getChat();
            
            // Iniciar indicador de digitação
            await chat.sendStateTyping();

            // Simular tempo de digitação (5 segundos)
            // Durante este tempo, vamos renovar o estado de digitação a cada 2 segundos
            const typingDuration = 5000; // 5 segundos
            const renewInterval = 2000; // Renovar a cada 2 segundos
            
            const startTime = Date.now();
            const typingInterval = setInterval(async () => {
                try {
                    await chat.sendStateTyping();
                } catch (error) {
                    console.log('Erro ao renovar estado de digitação:', error.message);
                }
            }, renewInterval);

            // Obter resposta da OpenAI (em paralelo com o delay)
            const [aiResponse] = await Promise.all([
                this.getOpenAIResponse(message.from, message.body),
                new Promise(resolve => setTimeout(resolve, typingDuration))
            ]);

            // Parar o intervalo de digitação
            clearInterval(typingInterval);

            // Enviar resposta
            await message.reply(aiResponse);

        } catch (error) {
            console.error('❌ Erro ao processar mensagem:', error);
            await message.reply('🔧 Desculpe, ocorreu um erro ao processar sua mensagem. Tente novamente.');
        }
    }

    async getOpenAIResponse(userId, userMessage) {
        try {
            // Obter histórico da conversa do usuário
            let conversation = this.conversationHistory.get(userId) || [];

            // Limitar tamanho da mensagem do usuário para economizar tokens
            const trimmedMessage = userMessage.length > 200 ? 
                userMessage.substring(0, 200) + '...' : userMessage;

            // Adicionar mensagem do usuário ao histórico
            conversation.push({
                role: 'user',
                content: trimmedMessage
            });

            // Manter apenas os últimos turnos da conversa para economizar tokens
            if (conversation.length > this.openaiConfig.maxHistoryTurns) {
                conversation = conversation.slice(-this.openaiConfig.maxHistoryTurns);
            }

            // Adicionar mensagem do sistema no início se for a primeira mensagem
            const messages = [];
            if (conversation.length === 1) {
                messages.push({
                    role: 'system',
                    content: 'Você é o Guri Virtual, um assistente de IA do WhatsApp. Responda de forma MUITO CONCISA em no máximo 50 palavras. Seja direto, útil e use emojis moderadamente. Evite explicações longas. Se apresente apenas na primeira mensagem.'
                });
            }
            
            // Adicionar histórico da conversa
            messages.push(...conversation);

            // Fazer requisição para a API da OpenAI
            const response = await axios.post(
                `${this.openaiConfig.baseURL}/chat/completions`,
                {
                    model: this.openaiConfig.model,
                    messages: messages,
                    max_tokens: parseInt(this.openaiConfig.maxTokens) || 100,
                    temperature: parseFloat(this.openaiConfig.temperature) || 0.7
                },
                {
                    headers: {
                        'Authorization': `Bearer ${this.openaiConfig.apiKey}`,
                        'Content-Type': 'application/json'
                    }
                }
            );

            // Extrair resposta do modelo
            const aiMessage = response.data.choices[0].message.content;

            // Garantir que a resposta não seja muito longa (backup)
            const finalMessage = this.trimResponse(aiMessage);

            // Adicionar resposta do assistente ao histórico
            conversation.push({
                role: 'assistant',
                content: finalMessage
            });

            // Salvar histórico atualizado
            this.conversationHistory.set(userId, conversation);

            return finalMessage;

        } catch (error) {
            console.error('❌ Erro na API da OpenAI:', error.response?.data || error.message);
            
            if (error.response?.status === 401) {
                return '🔑 Erro de autenticação. Verifique sua chave de API.';
            } else if (error.response?.status === 429) {
                return '⏰ Limite excedido. Tente em alguns minutos.';
            } else if (error.response?.status === 400) {
                return '❌ Erro na requisição. Reformule sua mensagem.';
            }
            
            return '🤖 Erro temporário. Tente novamente.';
        }
    }

    

   

    trimResponse(text) {
        // Garantir que a resposta não exceda ~50 palavras
        const words = text.split(' ');
        if (words.length > 50) {
            return words.slice(0, 50).join(' ') + '...';
        }
        return text;
    }

    // Método para limpar histórico automaticamente (executar periodicamente)
    cleanupHistory() {
        // Limpar conversas inativas há mais de 1 hora
        const oneHourAgo = Date.now() - (60 * 60 * 2000);
        
        for (const [userId, conversation] of this.conversationHistory.entries()) {
            // Se não tem timestamp, adicionar agora
            if (!conversation.lastActivity) {
                conversation.lastActivity = Date.now();
                continue;
            }
            
            // Remover conversas antigas
            if (conversation.lastActivity < oneHourAgo) {
                this.conversationHistory.delete(userId);
                console.log(`🧹 Histórico limpo para usuário: ${userId}`);
            }
        }
    }

    async start() {
        console.log('🚀 Iniciando WhatsApp Bot (Modo Econômico)...');
        
        // Verificar se a chave da API está configurada
        if (!process.env.OPENAI_API_KEY) {
            console.error('❌ OPENAI_API_KEY não está configurada no arquivo .env');
            process.exit(1);
        }

        // Configurar limpeza automática do histórico a cada 30 minutos
        setInterval(() => {
            this.cleanupHistory();
        }, 30 * 60 * 1000);

        console.log(`📊 Configuração otimizada:
        - Modelo: ${this.openaiConfig.model}
        - Máx tokens: ${this.openaiConfig.maxTokens} (~50 palavras)
        - Histórico: ${this.openaiConfig.maxHistoryTurns} turnos
        - Limpeza automática: 120 min`);

        // Inicializar cliente WhatsApp
        await this.client.initialize();
    }

    async stop() {
        console.log('🛑 Parando WhatsApp Bot...');
        await this.client.destroy();
    }
}

// Inicializar e executar o bot
const bot = new WhatsAppOpenAIBot();

// Tratar sinais de interrupção
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

// Iniciar o bot
bot.start().catch(error => {
    console.error('❌ Erro ao iniciar o bot:', error);
    process.exit(1);
});

module.exports = WhatsAppOpenAIBot;