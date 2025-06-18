require('dotenv').config();
const { Client, LocalAuth } = require('whatsapp-web.js');
const qrcode = require('qrcode-terminal');
const fetch = (...args) => import('node-fetch').then(({default: fetch}) => fetch(...args));

const OPENAI_API_KEY = process.env.OPENAI_API_KEY;
const OPENAI_API_URL = 'https://api.openai.com/v1/chat/completions';

// Inicializa o cliente WhatsApp
const client = new Client({
  authStrategy: new LocalAuth(),
});

client.on('qr', (qr) => {
  qrcode.generate(qr, { small: true });
  console.log('Escaneie o QR code acima para autenticar no WhatsApp.');
});

client.on('ready', () => {
  console.log('Bot está pronto!');
});

// Prompt de comportamento customizável para a IA
const SYSTEM_PROMPT = 'Você é um assistente de WhatsApp inteligente, educado, objetivo e responde sempre em português do Brasil. Na primeira mensagem sempre deve se apresentar como O Filhinho do Papai';

// Controle de contatos que já receberam a mensagem de boas-vindas
const welcomedContacts = new Set();

client.on('message', async (message) => {
  console.log('Mensagem recebida:', message.body);

  // Mensagem de boas-vindas estática para a primeira mensagem de cada contato
  if (!welcomedContacts.has(message.from)) {
    const welcomeMsg = 'Buenas';
    console.log('Enviando mensagem de boas-vindas para:', message.from);
    await client.sendMessage(message.from, welcomeMsg);
    welcomedContacts.add(message.from);
  }

  if (message.body.startsWith('!ai ')) {
    const prompt = message.body.replace('!ai ', '');
    console.log('Prompt enviado ao GPT:', prompt);
    try {
      let responseText = '';
      let gptRawResponse = null;
      // Tenta deepseek-chat, se falhar tenta gpt-3.5-turbo
      for (const model of ['deepseek-chat', 'gpt-3.5-turbo']) {
        try {
          console.log(`Enviando para modelo: ${model}`);
          const res = await fetch(OPENAI_API_URL, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${OPENAI_API_KEY}`,
            },
            body: JSON.stringify({
              model,
              messages: [
                { role: 'system', content: SYSTEM_PROMPT },
                { role: 'user', content: prompt },
              ],
            }),
          });
          const data = await res.json();
          gptRawResponse = data;
          console.log('Resposta bruta da OpenAI:', JSON.stringify(data, null, 2));
          if (data.choices && data.choices[0] && data.choices[0].message && data.choices[0].message.content) {
            responseText = data.choices[0].message.content;
            console.log('Resposta processada da OpenAI:', responseText);
            break;
          } else {
            console.log('Resposta inesperada da OpenAI:', JSON.stringify(data));
          }
        } catch (err) {
          console.log(`Erro com modelo ${model}:`, err.message);
        }
      }
      if (!responseText) responseText = 'Não foi possível obter resposta da OpenAI.';
      console.log('Resposta encaminhada para o WhatsApp:', responseText);
      await client.sendMessage(message.from, responseText);
    } catch (err) {
      console.error('Erro ao acessar a OpenAI:', err);
      await client.sendMessage(message.from, 'Erro ao acessar a OpenAI: ' + err.message);
    }
  }
});

client.initialize();
