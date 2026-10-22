# UmmJimalSeal

A command-line tool inspired by Umm al-Jimal, Jordan's 7th UNESCO World Heritage Site.

Just as the ancient city of Umm al-Jimal was preserved for its Authenticity and Integrity, this tool applies the same principles to your digital files. It seals a folder with SHA-256 hashes and an Ed25519 digital signature, then verifies it later to detect any modifications, additions, or deletions.

## Features

- Authenticity: Ed25519 digital signature ensures the manifest is the genuine original.
- Integrity: SHA-256 hashes prove that no file has been modified, added, or removed.
- HTML Reports: Generates a visually rich report to showcase the verification results.
- Cross-Platform: Works seamlessly on Windows, macOS, and Linux.

## Prerequisites

- Python 3.8 or higher.
- cryptography library.

## Installation

1. Clone the repository:
git clone https://github.com/your-username/UmmJimalSeal.git
cd UmmJimalSeal

2. Install the required dependencies:
pip install -r requirements.txt

## How It Works

1. Keygen (keygen): Generates an Ed25519 key pair. The private key is your secret seal, and the public key is shared for verification.
2. Seal (seal): Scans the folder, computes a SHA-256 hash for every file, creates a manifest, and signs it with your private key.
3. Verify (verify): Checks the digital signature first (Authenticity), then compares the hashes of the files (Integrity). It reports any changes found.

## Usage

1. Generate Keys
Run this once to create your private and public keys.
python umm_jimal_seal.py keygen --out keys
Keep private.pem secret. Share public.pem with anyone who needs to verify your files.

2. Seal a Folder
Seal a directory to create a signed manifest (json file).
python umm_jimal_seal.py seal my_folder --key keys/private.pem

3. Verify the Folder
Verify the folder's integrity and authenticity.
python umm_jimal_seal.py verify my_folder --pub keys/public.pem

4. Generate an HTML Report (Optional)
Generate a beautifully designed HTML report showing the status.
python umm_jimal_seal.py verify my_folder --pub keys/public.pem --html report.html

## Example Scenario

1. Create a test folder and a file inside it.
2. Seal the folder.
3. Modify the file's content (simulate tampering).
4. Run verify. The tool will output TAMPERED and highlight the modified file.

## Project Structure

UmmJimalSeal/
  umm_jimal_seal.py       # The main CLI tool
  requirements.txt        # Dependencies
  README.md               # Documentation
  assets/                 # Assets for HTML reports and documentation
    report_template.html
    about.html
    umm-al-jimal-1.jpg
    umm-al-jimal-2.jpg

## Why Umm al-Jimal?

"Umm al-Jimal was protected to stay authentic. I built a tool to protect your files the same way."

Built with pride from Jordan. #من_هون_أنا