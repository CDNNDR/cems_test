# setup.sh
mkdir -p .streamlit
cp /etc/secrets/secrets.toml ./.streamlit/
pip install -r requirements.txt
