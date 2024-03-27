from django.shortcuts import render
import requests
from bs4 import BeautifulSoup
from googletrans import Translator
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO
import os
from django.http import HttpResponse
import textwrap
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer
from django.template.loader import render_to_string
import yake

def display(request):
    urls = [
        "https://marathi.matrubharti.com/",
        "https://mr.wikipedia.org/wiki/%E0%A4%AE%E0%A5%80_%E0%A4%AE%E0%A4%B0%E0%A4%BE%E0%A4%A0%E0%A5%80"
    ]
    
    summaries = []
    for index, url in enumerate(urls, start=1):
        translated_text = translate_and_scrape(url)
        pdf_path = f"media/file{index}.pdf"
        save_to_pdf(translated_text, pdf_path)
        summary = summarize(translated_text)
        keywords=get_keywords(translated_text)
        summaries.append({
            'website': f"Website {index}",
            'summary': summary,
            'keywords': keywords
        })

    context = {'summaries': summaries}
    response = render_to_string('index.html', context)
    return HttpResponse(response)

def translate_and_scrape(url):
    req = requests.get(url)
    soup = BeautifulSoup(req.content, features='lxml')
    save_text = soup.get_text()
    return get_text_in_english(save_text)

def get_text_in_english(text):
    translator = Translator()
    translated_text = translator.translate(text, src='mr', dest='en').text
    return translated_text

def summarize(text):
    parser = PlaintextParser.from_string(text, Tokenizer("english"))
    summarizer = LsaSummarizer()
    summary = summarizer(parser.document, sentences_count=5)  
    summary = " ".join(str(sentence) for sentence in summary)
    
    return summary

def get_keywords(text):
    extracted_keywords = yake.KeywordExtractor()
    keywords = extracted_keywords.extract_keywords(text)
    word = [keyword[0] for keyword in keywords]
    return word

def save_to_pdf(text, file_path):
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    pdf.setTitle("Translated Text")

    lines = text.split('\n')
    max_line_length = 80
    wrapped_lines = []
    for line in lines:
        wrapped_lines.extend(textwrap.wrap(line, width=max_line_length))

    PAGE_WIDTH, PAGE_HEIGHT = letter
    TOP_MARGIN = 50
    BOTTOM_MARGIN = 50
    max_y = PAGE_HEIGHT - BOTTOM_MARGIN
    start_y = PAGE_HEIGHT - TOP_MARGIN
    line_height = 15
    max_y = 50
    for line in wrapped_lines:
        if start_y <= max_y:
            pdf.showPage()
            pdf.setFont("Helvetica", 12)
            start_y = PAGE_HEIGHT - TOP_MARGIN
        pdf.drawString(100, start_y, line)
        start_y -= line_height
    pdf.save()

    buffer.seek(0)
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "wb") as f:
        f.write(buffer.read())
    
    
    

   

