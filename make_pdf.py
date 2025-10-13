import os
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

# Output PDF name
output_pdf = "Project_Code.pdf"

# Folder path (current directory)
folder_path = "."

# Initialize PDF
pdf = canvas.Canvas(output_pdf, pagesize=A4)
width, height = A4

# Set fonts
pdf.setFont("Helvetica-Bold", 14)

y = height - 50

# Walk through all files in the folder
for root, dirs, files in os.walk(folder_path):
    for file in sorted(files):
        # Skip the PDF itself
        if file.endswith(".pdf") or file == os.path.basename(__file__):
            continue

        file_path = os.path.join(root, file)

        # Write file name
        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(50, y, f"File: {file_path}")
        y -= 20

        # Read file content
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.readlines()

        pdf.setFont("Courier", 10)
        for line in content:
            # Wrap long lines
            line = line.strip()
            if len(line) > 100:
                line_parts = [line[i:i+100] for i in range(0, len(line), 100)]
            else:
                line_parts = [line]

            for part in line_parts:
                pdf.drawString(50, y, part)
                y -= 12
                if y < 50:
                    pdf.showPage()
                    pdf.setFont("Courier", 10)
                    y = height - 50

        # Add spacing between files
        y -= 20
        if y < 50:
            pdf.showPage()
            y = height - 50

# Save PDF
pdf.save()
print(f"✅ PDF created: {output_pdf}")
