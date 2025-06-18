from FUNDAMENTALISTA.grafico.criar import Grafico
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import smtplib
import matplotlib.pyplot as plt
import os

class Email:
    def __init__(self):
            self.email_sender = "gabrielviero22@gmail.com"
            self.email_receiver = "gilneiviero97@gmail.com"
            self.email_password = "yscctdbdocoqaxhk"
            self.server = smtplib.SMTP('smtp.gmail.com', 587)
            self.server.starttls()
            self.server.login(self.email_sender, self.email_password)
            self.msg = MIMEMultipart()
            self.msg['From'] = self.email_sender
            self.msg['To'] = self.email_receiver
            self.msg['Subject'] = f'LISTA DE ATIVOS CARTEIRA UM'


    
    def mensagem(self,bons_para_compra, bons_para_venda, com_problema, preco, dados):
        grafico_instance = Grafico()
    
        # Agrupar os ativos por tempo
        ativos_por_tempo = {}
        preco_no_email = {}
        
        for ativo, tempos in dados.items():
            for tempo, dados_ativo in tempos.items():
                if tempo not in ativos_por_tempo:
                    ativos_por_tempo[tempo] = {}
                    preco_no_email[tempo] = {}
                ativos_por_tempo[tempo][ativo] = dados_ativo
                if ativo in preco and tempo in preco[ativo]:
                    preco_no_email[tempo][ativo] = preco[ativo][tempo]
        
        # Enviar e-mail separado para cada tempo
        for tempo, ativos in ativos_por_tempo.items():
            body = f"""
            TEMPOGRAFICO == {tempo}

            Lista de ativos para compra: {bons_para_compra}

            Lista de ativos para venda: {bons_para_venda}

            Lista de ativos sem dados: {com_problema}
            
            Preços:
            """
            for ativo, valor in preco_no_email[tempo].items():
                body += f"  Ativo: {ativo}, Preço: {valor}\n"
            
            # Criar a mensagem do e-mail
            msg = MIMEMultipart()
            msg['From'] = self.email_sender
            msg['To'] = self.email_receiver
            msg['Subject'] = f"Relatório de Ativos - Tempo {tempo}"
            msg.attach(MIMEText(body, 'plain'))
            
            # Anexar gráficos para cada ativo no tempo atual
            for ativo, tempos in dados.items():
                for tempo, dados_ativo in tempos.items():
                    filename = grafico_instance.cria_grafico_para_email(ativo, dados_ativo)
                    with open(filename, 'rb') as f:
                        img = MIMEImage(f.read())
                        img.add_header("Content-Disposition", "attachment", filename=filename)
                        msg.attach(img)
                    os.remove(filename)  # Excluir o arquivo após anexá-lo
            
            # Enviar o e-mail
            self.server.sendmail(self.email_sender, self.email_receiver, msg.as_string())
        
        # Fechar a conexão do servidor após enviar todos os e-mails
        self.server.quit()