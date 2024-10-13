
import streamlit as st
from rag_pipeline import get_email
from PIL import Image
import base64

hide_streamlit_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

#dictionary with roles
def new_chat():
    st.session_state.messages = [
        {"role": "assistant", "content": "How can I help you?"}
    ]



message_style = """
    <style>
    .chat-box {
        display: flex;
        align-items: flex-start;
        margin-bottom: 15px;
    }
    .chat-icon {
        background-color: #f5f5f5;
        color: #ffffff;
        border-radius: 50%;
        padding: 10px;
        margin-right: 15px;
        font-size: 20px;
        height: 50px;
        width: 50px;
        display: flex;
        justify-content: center;
        align-items: center;
    }
    .chat-message {
        background-color: #f5f5f5;
        padding: 15px;
        border-radius: 8px;
        font-family: 'Courier New', Courier, monospace;
        width: 100%;
        box-shadow: 0px 1px 4px rgba(0, 0, 0, 0.2);
    }
    body {
        background-color: #D84B50;
        padding-top: 0px;   /* Remove padding from the top of the page */
        margin-top: 0px;    /* Remove margin from the top of the page */
    }
    .main-container {
        background-color: white;
        width: 60%;  /* Adjust this to control the width of the white box */
        margin: 0 auto;
        padding: 20px;
        border-radius: 8px;
        box-shadow: 0px 1px 4px rgba(0, 0, 0, 0.2);
    }
    .image-container img {
        margin: 0;  /* Remove margin */
        padding: 0; /* Remove padding */
        display: block;  /* Ensure the image takes the full width */
    }
    </style>
"""

st.markdown(message_style, unsafe_allow_html=True)

# with st.sidebar:
#     st.sidebar.button(
#         "New chat",
#         on_click=new_chat,
#         help="Clear chat history and start a new chat",
#     )

#     st.header("Settings")




# Title
# Center the image and title using HTML and markdown
st.image("/root/Challenge-4-LLM-for-Event-Comms/datasport-4-1250x333.jpeg")
# st.title("📧 DataSports Chatbot")
# st.caption("DataSports Customer Support")



# Display the large heading and underline
st.markdown('<div class="underline"></div>', unsafe_allow_html=True)

# Display the FAQ text with a link
st.markdown(
    """
    <div class="faq-text">
    Have you checked our <a href="https://www.datasport.com/de/fuer-sportler/faq/">FAQ</a>? You will find many interesting answers that could resolve your issue.<br><br>
    Still have questions? Feel free to send us your message using the form below.
    <br><br>
    </div>
    """,
    unsafe_allow_html=True
)

# Still have questions? Feel free to send us your message using the form below. <br>For simpler inquiries, our Chatbot will provide a quick response, while more detailed or personal questions will be forwarded to our team for personalized support.
#     This ensures that our responses are as quick as our customers!
#     <br><br>

# Info
# st.markdown(
#     """
#     <div style="background-color: #e9f5fb; padding: 10px; border-radius: 5px;">
#     <strong>Do you need help or have any questions?</strong><br>
#     Please use the form below to share your request.<br><br>
#     For simpler inquiries, our Chatbot will provide a quick response, while more detailed or personal questions will be forwarded to our team for personalized support.
#     This ensures that our responses are as quick as our customers!
#     </div>
#     """,
#     unsafe_allow_html=True
# )

# Text area
# Event field takes the full width
event = st.text_input("Event")

# First Name and Last Name share the same line
col1, col2 = st.columns(2)
with col1:
    first_name = st.text_input("First Name")
with col2:
    last_name = st.text_input("Last Name")

# Birthday and Address share the same line
col3, col4 = st.columns(2)
with col3:
    birthday = st.text_input("Birthday")
with col4:
    address = st.text_input("Address")

# E-Mail and Phone Number share the same line
col5, col6 = st.columns(2)
with col5:
    email = st.text_input("E-Mail")
with col6:
    phone = st.text_input("Phone Number")

# Message field takes the full width as a large box (keeping it as a text area)
message = st.text_area("Message", height=200)

# Concatenate the inputs into a single string
concatenated_text = f"""
Event: {event}
First Name: {first_name}
Last Name: {last_name}
Birthday: {birthday}
Address: {address}
E-Mail: {email}
Phone Number: {phone}
Message: {message}
"""

# Function to trim the response
def trim_response(response):
    # Find the index of "Your DataSport Team" to remove anything after it
    split_marker = "Your DataSport Team"
    
    if split_marker in response:
        response = response.split(split_marker)[0] + split_marker
    
    # Find the index of "Dear" and remove anything before it
    dear_marker = "Dear"
    
    if dear_marker in response:
        response = response.split(dear_marker, 1)[1]  # Keep everything starting from "Dear"
        response = dear_marker + response  # Re-add "Dear" at the beginning
    
    return response



# Function to convert image to base64
def image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

# Convert the DataSport logo to base64
image_path = "/root/Challenge-4-LLM-for-Event-Comms/DS_logo.png"  # Adjust the path as needed
logo_base64 = image_to_base64(image_path)


# Handle button click for form submission
if st.button("Submit"):
    # Generate the response only after the button is clicked
    with st.spinner("Thinking..."):
        response = get_email(concatenated_text)  # Assuming this function processes the input

    # Display only the assistant's response
    trimmed_response = trim_response(response)
    # Create a custom chat message display with icon
    formatted_response = f"""
    <div class="chat-box">
        <div class="chat-icon">
            <img src="data:image/jpeg;base64,{logo_base64}" alt="Assistant Icon">
        </div>
        <div class="chat-message">
            {trimmed_response.replace('\n', '<br>')}
        </div>
    </div>
    """

    # Display the styled response
    st.markdown(formatted_response, unsafe_allow_html=True)




# # Chat elements
# if "messages" not in st.session_state:
#     st.session_state["messages"] = [
#         {"role": "assistant", "content": "Let me read your email?"}
#     ]

# for msg in st.session_state.messages:
#     st.chat_message(msg["role"]).write(msg["content"])

# if "messages" not in st.session_state:
#     st.session_state["messages"] = []

#     st.session_state.messages.append({"role": "user", "content": email})
#     with st.chat_message("user"):
#         st.write(concatenated_text)

#         if concatenated_text:
#             st.write(concatenated_text)
#             st.session_state.messages.append(
#                 {"role": "assistant", "content": concatenated_text}
#             )
# # Chat elements
# if "messages" not in st.session_state:
#     st.session_state["messages"] = [
#         {"role": "assistant", "content": "How can I help you?"}
#     ]

# # Display all messages
# #for msg in st.session_state.messages:
# #    st.chat_message(msg["role"]).write(msg["content"])

# # If the user provides input, generate a response using `get_email`
# if concatenated_text:
#     st.session_state.messages.append({"role": "user", "content": concatenated_text})
#     with st.chat_message("user"):
#         st.write(concatenated_text)

#     # Generate a response using the get_email function
#     with st.chat_message("assistant"):
#         with st.spinner("Thinking ..."):
#             response = get_email(str(concatenated_text))  # Assuming get_email takes `transcript` as input

#         if response:
#             st.write(response)
#             st.session_state.messages.append(
#                 {"role": "assistant", "content": response}
#             )