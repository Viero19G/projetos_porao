const { Client, LocalAuth, MessageMedia } = require('whatsapp-web.js');
const qrcode = require('qrcode-terminal');
const axios = require('axios');
const FormData = require('form-data');
const fs = require('fs');
const path = require('path');
const express = require('express');

const app = express();
app.use(express.json());

const client = new Client({
    authStrategy: new LocalAuth({
        clientId: "whatsapp-ai-bot",
        dataPath: './session'
    }),
    puppeteer: {
        headless: true,
        args: [
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
            '--disable-accelerated-2d-canvas',
            '--no-first-run',
            '--no-zygote',
            '--single-process',
            '--disable-gpu'
        ]
    }
});

// Configurações
const API_URL = process.env.API_URL || 'http://localhost:8000';
const CONVERSATIONS_PATH = '/app/conversations';

// Ensure conversations directory exists
if (!fs.existsSync(CONVERSATIONS_PATH)) {
    fs.mkdirSync(CONVERSATIONS_PATH, { recursive: true });
}

// Generate QR Code
client.on('qr', (qr) => {
    console.log('QR Code gerado, escaneie com seu WhatsApp:');
    qrcode.generate(qr, { small: true });
});

// Client ready
client.on('ready', () => {
    console.log('WhatsApp Web está pronto!');
});

// Authentication failure
client.on('auth_failure', msg => {
    console.error('Falha na autenticação:', msg);
});

// Disconnected
client.on('disconnected', (reason) => {
    console.log('Cliente desconectado:', reason);
});

// Message handler
client.on('message', async (message) => {
    try {
        // Ignore group messages and status updates
        if (message.from.includes('@g.us') || message.from.includes('status@broadcast')) {
            return;
        }

        const contact = await message.getContact();
        const chat = await message.getChat();
        
        console.log(`Nova mensagem de ${contact.name || contact.pushname || message.from}: ${message.body}`);

        // Prepare message data
        const messageData = {
            phone_number: message.from.replace('@c.us', ''),
            contact_name: contact.name || contact.pushname || 'Unknown',
            message_type: message.type,
            message_body: message.body || '',
            timestamp: new Date().toISOString()
        };

        // Handle different message types
        let mediaData = null;
        
        if (message.hasMedia) {
            const media = await message.downloadMedia();
            
            if (media) {
                // Save media file temporarily
                const fileName = `${Date.now()}_${message.from.replace('@c.us', '')}_${message.type}`;
                const filePath = path.join('/tmp', fileName);
                
                fs.writeFileSync(filePath, media.data, 'base64');
                
                mediaData = {
                    filename: fileName,
                    mimetype: media.mimetype,
                    data: media.data,
                    filepath: filePath
                };
                
                messageData.has_media = true;
                messageData.media_type = message.type;
            }
        }

        // Send to AI API
        await sendToAI(messageData, mediaData, message);

    } catch (error) {
        console.error('Erro ao processar mensagem:', error);
    }
});

async function sendToAI(messageData, mediaData, originalMessage) {
    try {
        const formData = new FormData();
        
        // Add message data
        Object.keys(messageData).forEach(key => {
            formData.append(key, messageData[key]);
        });

        // Add media if exists
        if (mediaData) {
            const mediaBuffer = Buffer.from(mediaData.data, 'base64');
            formData.append('media_file', mediaBuffer, {
                filename: mediaData.filename,
                contentType: mediaData.mimetype
            });
        }

        const response = await axios.post(`${API_URL}/api/chat/process/`, formData, {
            headers: {
                ...formData.getHeaders(),
                'Content-Type': 'multipart/form-data'
            },
            timeout: 30000
        });

        if (response.data && response.data.response) {
            // Send AI response back to WhatsApp
            await sendResponse(originalMessage, response.data.response, response.data.media_response);
        }

        // Clean up temp file
        if (mediaData && mediaData.filepath && fs.existsSync(mediaData.filepath)) {
            fs.unlinkSync(mediaData.filepath);
        }

    } catch (error) {
        console.error('Erro ao enviar para API:', error.message);
        
        // Send error message to user
        await originalMessage.reply('Desculpe, ocorreu um erro ao processar sua mensagem. Tente novamente.');
        
        // Clean up temp file
        if (mediaData && mediaData.filepath && fs.existsSync(mediaData.filepath)) {
            fs.unlinkSync(mediaData.filepath);
        }
    }
}

async function sendResponse(originalMessage, textResponse, mediaResponse) {
    try {
        // Send text response
        if (textResponse) {
            await originalMessage.reply(textResponse);
        }

        // Send media response if exists
        if (mediaResponse) {
            const media = MessageMedia.fromFilePath(mediaResponse.filepath);
            await originalMessage.reply(media, undefined, { caption: mediaResponse.caption || '' });
            
            // Clean up media file
            if (fs.existsSync(mediaResponse.filepath)) {
                fs.unlinkSync(mediaResponse.filepath);
            }
        }
    } catch (error) {
        console.error('Erro ao enviar resposta:', error);
    }
}

// Health check endpoint
app.get('/health', (req, res) => {
    res.json({ status: 'ok', client_ready: client.info ? true : false });
});

// Start Express server
app.listen(3000, () => {
    console.log('Servidor Express rodando na porta 3000');
});

// Initialize WhatsApp client
client.initialize();

// Graceful shutdown
process.on('SIGINT', async () => {
    console.log('Desconectando cliente...');
    await client.destroy();
    process.exit(0);
});