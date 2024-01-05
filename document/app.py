from flask import Flask, request, render_template
import PyPDF2
import os

app = Flask(__name__)

# Your existing functions go here (extract_pdf_metadata, extract_metadata_from_folder)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    uploaded_files = request.files.getlist("file[]")
    results = []
    for file in uploaded_files:
        if file.filename.lower().endswith('.pdf'):
            metadata = extract_pdf_metadata(file)
            results.append((file.filename, metadata))
    return render_template('results.html', results=results)

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

# def extract_metadata_from_folder(folder_path):
#     metadata_list = []
#     for filename in os.listdir(folder_path):
#         if filename.lower().endswith('.pdf'):
#             file_path = os.path.join(folder_path, filename)
#             metadata = extract_pdf_metadata(file_path)
#             metadata_list.append((filename, metadata))
#     return metadata_list



if __name__ == '__main__':
    app.run(debug=True)
