#!/bin/bash

echo "Setting up VC Memo Backend Environment"
echo "====================================="

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Create .env file template
if [ ! -f ".env" ]; then
    echo "OPENAI_API_KEY=your_openai_api_key_here" > .env
    echo "Created .env file - please add your OpenAI API key"
fi

echo ""
echo "Setup complete! Next steps:"
echo "1. Edit .env and add your OpenAI API key"
echo "2. Run ./run_server.sh to start the server"
echo "3. Run python test_api.py to test the system"
