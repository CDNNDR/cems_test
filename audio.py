import streamlit as st
import openai
import os
import whisper
import base64

# Path where Render makes the secret files accessible
secrets_path = '/etc/secrets/secrets.toml'

if os.path.exists(secrets_path):
    st.secrets.load(secrets_path)
else:
    st.error("Secrets file not found!")


# Set the OpenAI API key
openai_api_key = st.secrets["openai_api_key"]
os.environ["OPENAI_API_KEY"] = openai_api_key
openai.api_key = openai_api_key

# Set the screen to full width by default
def wide_space_default():
    st.set_page_config(layout="wide")

# Call the function to apply the setting
wide_space_default()

# Load the Whisper model
model = whisper.load_model('small')  # You can choose 'base', 'small', etc.

# Initialize call "jars"
call_jars = {
    "book_visit": [],
    "cancel_visit": [],
    "complaint": [],
    "information": [],
    "payment_issue": [],
    "other": []
}

# Define possible keywords to map LLM responses to the correct jar
category_keywords = {
    "book_visit": ["book_visit", "prenotazione", "prenotare"],
    "cancel_visit": ["cancel_visit", "cancellazione", "disdire", "annullare"],
    "complaint": ["complaint", "lamentela", "problema"],
    "information": ["information", "informazioni", "info", "chiedere"],
    "payment_issue": ["payment_issue", "pagamento", "fattura"],
}

# Function to match LLM response to a jar category
def map_response_to_category(response):
    for category, keywords in category_keywords.items():
        for keyword in keywords:
            if keyword in response:
                return category
    return "other"

# Function to transcribe audio using Whisper
def transcribe_audio(file):
    try:
        result = model.transcribe(file, language='it')
        return result['text']
    except Exception as e:
        return f"Error during transcription: {e}"

# Function to analyze the text using OpenAI's API and classify the call
def classify_intent(transcript):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",  # Use the preferred model
            messages=[
                {"role": "system", "content": "Sei un assistente esperto in analisi delle chiamate del call center. Classifica il seguente testo in una delle categorie: 'book_visit', 'cancel_visit', 'complaint', 'information', 'payment_issue', 'other'."},
                {"role": "user", "content": f"Classifica questa chiamata: {transcript}"}
            ],
            max_tokens=500,
        )
        # Get the LLM's response
        classification_response = response['choices'][0]['message']['content'].strip().lower()
        # Map the LLM's response to one of the predefined categories
        return map_response_to_category(classification_response)
    except Exception as e:
        return f"Error during analysis: {e}"

# Function to add call to the appropriate jar
def add_call_to_jar(transcript, category):
    if category in call_jars:
        call_jars[category].append(transcript)
    else:
        call_jars["other"].append(transcript)

# Inject custom CSS to crop the image
st.markdown("""
    <style>
    /* Remove the default Streamlit padding */
    .css-18e3th9 {
        padding: 0;
    }

    /* Style the main content */
    .css-1lcbmhc {
        padding-top: 0;
    }

    /* Image as a cropped banner */
    .banner-image {
        width: 100%;
        height: 150px;
        object-fit: cover;
        object-position: center;
    }
    </style>
    """, unsafe_allow_html=True)

# Load and encode the image in base64
def get_base64_image(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

# Path to your image file
image_path = "logo.png"
image_base64 = get_base64_image(image_path)

# Display the cropped image as a banner
st.markdown(f'<img src="data:image/png;base64,{image_base64}" class="banner-image">', unsafe_allow_html=True)

# Main title
st.title('Analisi delle chiamate del call center', anchor='main-title')
st.caption("🚀 Carica delle chiamate telefoniche, l'assistente AI è in grado di riconoscere se si tratta di una prenotazione, cancellazione o altro. Si tratta di un test. Il sistema potrebbe essere lento in quanto sta girando in ambiente di test")

# Upload audio file
uploaded_file = st.file_uploader('Carica un file audio della chiamata', type=['mp3', 'wav', 'm4a', 'ogg'], key='file_uploader')

if uploaded_file is not None:
    # Show a loading spinner while processing
    with st.spinner('Elaborazione del file in corso...'):
        # Save the uploaded audio file
        with open('uploaded_audio_file.mp3', 'wb') as f:
            f.write(uploaded_file.getbuffer())

        # Transcribe the audio
        transcript = transcribe_audio('uploaded_audio_file.mp3')

        # If transcription is successful, classify the call
        if "Error" not in transcript:
            category = classify_intent(transcript)
            add_call_to_jar(transcript, category)

            st.write(f"Chiamata classificata come: {category}")
            st.write("Trascrizione della chiamata:")
            st.text_area("Transcription Result:", transcript, height=150)

            # Display the current state of the jars
            st.write("Jars attuali:")
            for jar, calls in call_jars.items():
                st.write(f"**{jar}**: {len(calls)} chiamate")

        else:
            st.write(transcript)  # Display the error if transcription fails

    st.success('Elaborazione completata!')
