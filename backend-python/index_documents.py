import os
import sys

# Tambahkan path ke folder app
sys.path.append(os.path.dirname(__file__))

from app.main import process_document

# Folder tempat PDF disimpan
pdf_folder = "./documents"

# Buat folder documents jika belum ada
if not os.path.exists(pdf_folder):
    os.makedirs(pdf_folder)
    print(f"📁 Folder '{pdf_folder}' dibuat. Pindahkan PDF ke sini!")
    sys.exit(0)

# Loop semua file PDF
pdf_files = [f for f in os.listdir(pdf_folder) if f.endswith(".pdf")]

if not pdf_files:
    print("❌ Tidak ada file PDF di folder 'documents/'")
    print("📂 Pindahkan file PDF ke folder documents/ dulu!")
    sys.exit(0)

print(f"📄 Menemukan {len(pdf_files)} file PDF:")
for f in pdf_files:
    print(f"   - {f}")

print("\n🚀 Memulai indexing...\n")

for filename in pdf_files:
    file_path = os.path.join(pdf_folder, filename)
    print(f"📄 Indexing: {filename}...")
    try:
        process_document(file_path, filename)
        print(f"✅ {filename} selesai!\n")
    except Exception as e:
        print(f"❌ Error indexing {filename}: {e}\n")

print("🎉 Semua dokumen selesai di-index!")