import streamlit as st
import os
import re
import hashlib
import fitz  # PyMuPDF
from PIL import Image, ImageEnhance
from pyzbar.pyzbar import decode
import PyPDF2
import altair as alt
import io


# Assuming the rest of your functions are defined above (calculate_hash, upload_document, extract_gstin, etc.)

# Set the upload folder and maximum content length
UPLOAD_FOLDER = 'uploads/'
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB upload limit
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

st.title('PDF Upload and Analysis')

def calculate_hash(file_path):
    hasher = hashlib.sha256()
    with open(file_path, 'rb') as file:
        buf = file.read()
        hasher.update(buf)
    return hasher.hexdigest()
def upload_document(file_path, uploads_folder):
    new_doc_hash = calculate_hash(file_path)

    for filename in os.listdir(uploads_folder):
        existing_file_path = os.path.join(uploads_folder, filename)
        if os.path.isfile(existing_file_path):
            existing_file_hash = calculate_hash(existing_file_path)
            if new_doc_hash == existing_file_hash:
                return False, "This document already exists."

    return True, "Document uploaded successfully."


def extract_gstin(text):
    # GSTIN regex pattern: 2 digits, 10 alphanumeric, 1 digit, 1 alphanumeric, 1 digit
    pattern = r'\b\d{2}[A-Z]{5}\d{4}[A-Z]{1}\d{1}[Z]{1}[A-Z\d]{1}\b'
    matches = re.findall(pattern, text)
    return matches[0] if matches else None




def extract_text_from_pdf(pdf_path):
    text = ""
    doc = fitz.open(pdf_path)

    for page_num in range(doc.page_count):
        page = doc.load_page(page_num)
        text += page.get_text("text")

    doc.close()
    return text

def extract_pdf_metadata(file_path):
    try:
        with open(file_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            metadata = reader.metadata
            document_info = {
                'Title': metadata.get('/Title', 'Not available'),
                'Author': metadata.get('/Author', 'Not available'),
                'Subject': metadata.get('/Subject', 'Not available'),
                'Keywords': metadata.get('/Keywords', 'Not available'),
                'Creator': metadata.get('/Creator', 'Not available'),
                'Producer': metadata.get('/Producer', 'Not available'),
                'CreationDate': metadata.get('/CreationDate', 'Not available'),
                'ModDate': metadata.get('/ModDate', 'Not available'),
                'Trapped': metadata.get('/Trapped', 'Not available')
            }
            return document_info
    except Exception as e:
        return f"An error occurred: {e}"

# Function to check PDF metadata
def check_metadata(metadata):
    valid_authors = ["Not available", "Bharti Airtel Limited"]
    valid_creators = ["Chromium", "Bharti Airtel Limited",
                      "JasperReports Library version 6.14.0-2ab0d8625be255bf609c78e1181801213e51db8f",
                      "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Mobile Safari/537.36",
                      "dvips(k) 5.95a Copyright 2005 Radical Eye Software", "Not available"]
    valid_producers = ["GPL Ghostscript 8.70", "Skia/PDF m119",
                       "iText 2.1.7 by 1T3XT; modified using iText® 7.1.12 ©2000-2020 iText Group NV (AGPL-version)",
                       "OpenPDF 1.3.28", "Not available"]

    author = metadata.get('Author', 'Not available')
    creator = metadata.get('Creator', 'Not available')
    producer = metadata.get('Producer', 'Not available')
    creation_date = metadata.get('CreationDate', '')
    mod_date = metadata.get('ModDate', '')

    dates_match = creation_date == mod_date
    author_ok = author in valid_authors
    creator_ok = creator in valid_creators
    producer_ok = producer in valid_producers

    return author_ok and creator_ok and producer_ok and dates_match
def extract_images_and_decode_qr(pdf_path, output_folder):
    doc = fitz.open(pdf_path)
    os.makedirs(output_folder, exist_ok=True)
    qr_data = []

    for page_num in range(doc.page_count):
        page = doc.load_page(page_num)
        for img_index, img in enumerate(page.get_images(full=True)):
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            if not image_bytes:
                continue  # Skip if no image bytes were extracted
            
            try:
                image = Image.open(io.BytesIO(image_bytes))
                # Enhance and decode image for QR code
                enhancer = ImageEnhance.Contrast(image)
                enhanced_image = enhancer.enhance(2.0)
                resized_image = enhanced_image.resize((300, 300))
                decoded_objects = decode(resized_image)
                for obj in decoded_objects:
                    qr_data.append(obj.data.decode("utf-8"))
            except Exception as e:
                print(f"An error occurred while processing an image: {e}")
                continue  # Skip this image and move to the next one

    doc.close()
    return qr_data

uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")

if uploaded_file is not None:
    # Calculate hash of the uploaded file to check for duplicates
    bytes_data = uploaded_file.getvalue()  # Use getvalue() to read bytes directly
    hash_of_uploaded_file = hashlib.sha256(bytes_data).hexdigest()

    # Check if file with the same hash exists
    is_duplicate = any(
        hash_of_uploaded_file == calculate_hash(os.path.join(UPLOAD_FOLDER, existing_filename))
        for existing_filename in os.listdir(UPLOAD_FOLDER)
    )

    if is_duplicate:
        st.error("This document already exists.")
    else:
        file_path = os.path.join(UPLOAD_FOLDER, uploaded_file.name)
        
        # Save the uploaded PDF if it's not a duplicate
        with open(file_path, 'wb') as f:
            f.write(bytes_data)
        
        # Continue processing the PDF
        metadata = extract_pdf_metadata(file_path)
        is_good = check_metadata(metadata)
        qr_contents = extract_images_and_decode_qr(file_path, UPLOAD_FOLDER)
        pdf_text = extract_text_from_pdf(file_path)  # Extract text from the PDF
        gstin = extract_gstin(pdf_text)
        
        # Display results
        st.success("Document uploaded successfully.")
        st.json(metadata)
        if is_good:
            st.success("Metadata is good.")
        else:
            st.warning("Metadata check failed.")
        
        st.write("QR Contents:")
        st.write(qr_contents)
        
        st.write("Extracted Text:")
        st.write(pdf_text)
        
        if gstin:
            st.write("Extracted GSTIN:")
            st.write(gstin)
