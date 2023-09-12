#pip install nltk
#pip install langdetect
#pip install iso639
#pip install fpdf
import nltk
nltk.download('stopwords', download_dir=r'dados\nltk_data')

'''Arquivo de pré-processamento de dados.'''
import pandas as pd
import re
import nltk
from nltk.corpus import stopwords 
from nltk.stem import PorterStemmer, SnowballStemmer
from langdetect import detect
import iso639
import unicodedata

nltk.data.path.append(r".\dados\nltk_data")

def process_string(string):
    """
    Função que realiza pré-processamento em um texto.

    Args:
        string (str): O texto a ser pré-processado.
        idioma (str, optional): O idioma da stopword list e do stemmer. Padrão é 'portuguese'.

    Returns:
        str: O texto pré-processado.
    """
    # Converte para minúsculas
    string = string.lower()

    # Prepara o regex para remover pontuações
    punct_regex = re.compile('[^\w\s]')

    # Remove pontuações
    string = re.sub(punct_regex, '', string)

    #Remove acentos
    string = unicodedata.normalize('NFKD', string).encode('ASCII', 'ignore').decode('ASCII')

    #Prepara regex para remover números
    num_regex = re.compile('\d+')

    # Remove números
    string = re.sub(num_regex, '', string)

    # Detecta o idioma do texto
    idioma = (iso639.to_name(detect(string))).lower()

    print('Idioma detectado:', idioma)

    # Define as stopwords de acordo com o idioma
    # Portugues
    if idioma == 'portuguese':
        stop_words = set(stopwords.words('portuguese'))
        stemmer = PorterStemmer()
    # Inglês
    elif idioma == 'english':
        stop_words = set(stopwords.words('english'))
        stemmer = SnowballStemmer('english')
    # Outros idiomas
    else:
        try:
            stop_words = set(stopwords.words(idioma))
            stemmer = SnowballStemmer(idioma)
        except:
            stop_words = set(stopwords.words('portuguese'))
            stemmer = PorterStemmer()
            # raise ValueError(f"Identificado idioma:{idioma}. Idioma deve ser 'portuguese' ou 'english'.")
    
    # Remove stopwords    
    string = ' '.join([word for word in string.split() if word not in stop_words])

    # Aplica stemming
    string = ' '.join([stemmer.stem(word) for word in string.split()])

    #Remove palavras com menos de 3 caracteres
    # string = ' '.join([word for word in string.split() if len(word) > 3])
    string = [word for word in string.split() if len(word) > 3]
    
    return string

#Carregar paginas do pdf e salvar as strings
import PyPDF2

def extrair_texto_pdf(nome_arquivo, num_max_tokens=1000):
    with open(nome_arquivo, 'rb') as arquivo:
        leitor = PyPDF2.PdfReader(arquivo)
        numero_paginas = len(leitor.pages)
        print('Numero de paginas: ', numero_paginas)
        texto = {}
        for pagina in range(numero_paginas):
            print('Extraindo Página: ', pagina)
            pagina_atual = leitor.pages[pagina]
            texto_extraido = pagina_atual.extract_text()
            texto_extraido = process_string(texto_extraido)
            tokens = [' '.join(texto_extraido[i:i+num_max_tokens]) for i in range(0, len(texto_extraido), num_max_tokens-10)]
            texto[pagina] = tokens
        print('Numero de páginas extraidas: ', len(texto))
        return texto

nome_arquivo = 'pythonlearn.pdf' # Substitua pelo nome do seu arquivo PDF
texto_extraido = extrair_texto_pdf(nome_arquivo)

from tenacity import retry, stop_after_attempt
import openai
import time
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv('API_KEY')
openai.api_key = API_KEY
@retry(stop=stop_after_attempt(4))
def get_resume(text, *kwargs):
   
    prompt = f"Resuma o texto abaixo de forma bem didática e apenas com os principais pontos para entendimento: \n{text}"
    completion = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    max_tokens=350,
    temperature=0.5,
    messages=[
        {"role": "user", "content": prompt}
    ]
    )
    return completion.choices[0].message['content']

start = time.time()
r = []
for pagina in texto_extraido:
    print('Resumindo página: ', pagina)
    for token in texto_extraido[pagina]:
        r.append(get_resume(token))
end = time.time()
print(f"Tempo de execução da função get_resume: {end - start:.2f}s")

from fpdf import FPDF

pdf = FPDF()
pdf.add_page()
pdf.set_font("Arial", size=12)

for pagina in r:
    pdf.multi_cell(0, 10, txt=pagina, align="L")
    pdf.ln()  # Adiciona uma nova linha após cada chamada ao MultiCell

pdf.output("resumo.pdf")