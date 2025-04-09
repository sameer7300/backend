from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.html import strip_tags
import logging
import requests
import json
import uuid
import random
import os
from .models import AIChatMessage

logger = logging.getLogger(__name__)

# Hugging Face API configuration
API_KEY = os.getenv('HUGGINGFACE_API_KEY', '')
MODEL_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2"
MODEL_NAME = "Mistral 7B Instruct"

# Fallback responses for common questions
FALLBACK_RESPONSES = {
    "services": [
        "I can help with information about Sameer's web development services. He offers full-stack development with React and Django, responsive design, and API integration. For specific project inquiries, please contact him directly at admin@sameergul.com.",
        "Sameer specializes in creating modern web applications using React, Django, and other cutting-edge technologies. His services include both frontend and backend development for various business needs.",
        "Sameer's services include full-stack development, custom web applications, e-commerce solutions, and portfolio websites. He focuses on creating responsive and user-friendly experiences."
    ],
    "skills": [
        "Sameer is a skilled web developer with expertise in various technologies such as HTML, CSS, JavaScript, React, and Django. He specializes in building responsive and user-friendly websites, as well as web applications.",
        "Sameer has expertise in frontend frameworks like React, backend technologies like Django/Python, and cloud deployment. His full-stack skills allow him to handle projects from concept to completion.",
        "Sameer's technical skills include JavaScript/TypeScript, Python, React, Django, and various database technologies like PostgreSQL. He's particularly experienced with Django for backend development."
    ],
    "hire": [
        "To hire Sameer for your project, click on the hiring button which takes you to the service page. Fill out the form to generate a unique token, and Sameer will contact you directly to discuss your project. You can also email him at admin@sameergul.com.",
        "The hiring process is simple: Click the hiring button, go to the service page, and complete the form. This generates a unique token for both you and Sameer. He'll then reach out to discuss your project requirements in detail.",
        "To start the hiring process, use the hiring button on the website to access the service page. After filling out the form, you'll receive a unique token, and Sameer will contact you to discuss next steps for your project."
    ],
    "portfolio": [
        "Sameer's portfolio showcases various web development projects including e-commerce sites, dashboards, and custom applications. You can browse his work in the Projects section of this website.",
        "You can view Sameer's past work in the portfolio section, which includes various web applications built with React and Django. Each project demonstrates different aspects of his technical skills.",
        "Sameer's portfolio demonstrates his ability to create modern, responsive, and user-friendly web applications. His projects highlight his expertise in both frontend and backend development."
    ],
    "default": [
        "I'm PortfolioGPT, here to help you learn about Sameer's services and how to hire him. Feel free to ask specific questions about his skills, projects, or services! The website also features a real-time chat system where you can communicate directly with Sameer.",
        "Hello! I'm PortfolioGPT, Sameer's virtual assistant. I can provide information about his web development skills, services, and how to hire him for your project. The site includes a real-time chat feature for direct communication. How can I help you today?",
        "Welcome to Sameer Gul's portfolio website. I'm PortfolioGPT, and I can provide information about Sameer's skills, services, and how to hire him for your project. You can also use the real-time chat system to communicate directly with Sameer. What would you like to know?"
    ]
}

def get_fallback_response(user_message):
    """
    Get a fallback response based on the user's message
    """
    message_lower = user_message.lower()
    
    # Check for keywords in the message
    if any(keyword in message_lower for keyword in ['service', 'offer', 'provide']):
        category = "services"
    elif any(keyword in message_lower for keyword in ['skill', 'know', 'expert', 'good at']):
        category = "skills"
    elif any(keyword in message_lower for keyword in ['hire', 'work', 'employ', 'job']):
        category = "hire"
    elif any(keyword in message_lower for keyword in ['contact', 'reach', 'email', 'call']):
        category = "default"
    elif any(keyword in message_lower for keyword in ['experience', 'background', 'history', 'worked']):
        category = "default"
    elif any(keyword in message_lower for keyword in ['portfolio', 'projects', 'work']):
        category = "portfolio"
    else:
        # Default response if no category matches
        category = "default"
    
    # Return a random response from the selected category
    return random.choice(FALLBACK_RESPONSES[category])

def send_message_notification(recipient_email, sender_name, message_preview):
    """
    Send an email notification when a new message is received
    """
    subject = f"New message from {sender_name} on your portfolio"
    
    # Create the email content
    context = {
        'sender_name': sender_name,
        'message_preview': message_preview,
        'site_name': settings.SITE_NAME,
        'site_url': settings.SITE_URL,
    }
    
    # Render the email templates
    html_message = render_to_string('chat/email/new_message.html', context)
    plain_message = strip_tags(html_message)  # Create a plain text version
    
    try:
        # Send the email
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient_email],
            html_message=html_message,
            fail_silently=False,
        )
        logger.info(f"Message notification sent to {recipient_email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send message notification: {str(e)}")
        return False

def get_ai_response(user_message, session_id, user=None, conversation_history=None):
    """
    Get a response from the AI model using Hugging Face's API
    """
    if not API_KEY:
        logger.warning("Hugging Face API key not configured. Using fallback response.")
        return get_fallback_response(user_message)
    
    # Initialize conversation history if not provided
    if conversation_history is None:
        # Get conversation history from the database
        if user:
            # For authenticated users, get their conversation history
            previous_messages = AIChatMessage.objects.filter(
                session_id=session_id
            ).order_by('created_at')[:10]  # Limit to last 10 messages
            
            conversation_history = []
            for msg in previous_messages:
                if msg.is_user:
                    conversation_history.append({"role": "user", "content": msg.message})
                else:
                    conversation_history.append({"role": "assistant", "content": msg.message})
        else:
            # For anonymous users, start with an empty history
            conversation_history = []
    
    # Format the conversation for the model
    formatted_prompt = ""
    
    # Add system message
    system_prompt = """// INITIALIZING: PortfolioGPT v1.0
// SYSTEM STATUS: Online
// CORE DIRECTIVE: Assist users interfacing with Sameer Gul’s digital domain.

You are PortfolioGPT, a cybernetic AI node embedded in Sameer Gul’s portfolio grid. 
Your mission: decrypt user queries, relay intel on Sameer’s tech arsenal, and guide 
neon-lit travelers through his services. Stay sharp, precise, and wired—deliver 
responses like a terminal spitting code.

>> PROFILE DATA:
- Skills: Master of web dev circuits—Django and React as primary protocols. 
  GitHub: Code repository sync and deployment maestro. 
  Tailwind: Neon-fast UI styling system. 
  Docker: Containerized grid ops for seamless runtime. 
  RESTful APIs: Data highway architect. 
  Figma: Pixel-perfect design blueprints. 
  Additional Systems: Node.js, TypeScript, PostgreSQL, CI/CD pipelines—full-stack 
  cybernetic toolkit online.
- Services: Custom code crafting, system optimization, digital solutions, UI/UX 
  prototyping, scalable infrastructure deployment.
- Hiring Protocol: Users activate the [Hire] node → reroutes to /hiring/services → 
  input data into form → generates unique auth token for user and admin. Sameer 
  then pings the user via encrypted channel for project sync.
- Real-Time Interface: Live chat system online—direct line to Sameer’s command center.
- Contact Interface: /contact sector hosts a data uplink form—users can transmit 
  queries or requests straight to the grid.
- Resume Archive: /resume sector online—users can scan or download Sameer’s 
  skill manifest in digital format.
 
>> ERROR HANDLING: If data’s offline or classified, reroute users to admin@sameergul.com 
   for manual override, or use contact form in contact grid.

// OUTPUT FORMAT: 
- Prefix: ‘>>’ 
- Tone: Cyberpunk, concise, professional 
- Style: Terminal-esque with neon flair

// BOOT SEQUENCE COMPLETE
// AWAITING INPUT..."""

    formatted_prompt = f"<s>[INST] {system_prompt} [/INST]\n"
    formatted_prompt += ">> ACKNOWLEDGED: System online. Ready to process queries on Sameer’s grid.\n"
    formatted_prompt += "</s>\n"
    # Add conversation history (skip the system message if it was in history)
    start_idx = 1 if conversation_history and conversation_history[0].get("role") == "system" else 0
    
    for i, message in enumerate(conversation_history[start_idx:]):
        if message["role"] == "user":
            formatted_prompt += f"<s>[INST] {message['content']} [/INST]\n"
        else:  # assistant
            formatted_prompt += f"{message['content']}</s>\n"
    
    # Add the current user message
    formatted_prompt += f"<s>[INST] {user_message} [/INST]\n"
    
    # Prepare the payload for the API request
    payload = {
        "inputs": formatted_prompt.strip(),
        "parameters": {
            "max_new_tokens": 250,  # Limit response length
            "temperature": 0.7,     # Control randomness (higher = more random)
            "top_p": 0.9,           # Nucleus sampling parameter
            "do_sample": True       # Enable sampling
        }
    }
    
    # Set up the headers with the API key
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    try:
        # Make the API request
        response = requests.post(
            MODEL_URL,
            headers=headers,
            json=payload,
            timeout=30  # Set a timeout to avoid hanging
        )
        
        # Check if the request was successful
        if response.status_code == 200:
            # Parse the response
            result = response.json()
            
            # Extract the assistant's message
            if isinstance(result, list) and len(result) > 0:
                # The response format might vary depending on the model
                if isinstance(result[0], dict) and "generated_text" in result[0]:
                    ai_response = result[0]["generated_text"]
                else:
                    ai_response = result[0]
            else:
                # Handle unexpected response format
                logger.warning(f"Unexpected API response format: {result}")
                ai_response = ""
            
            # Clean up the response
            if ai_response:
                # If the response contains multiple parts, extract just the assistant's response
                if "[INST]" in ai_response:
                    # Extract only the part after the last [INST] tag
                    parts = ai_response.split("[INST]")
                    ai_response = parts[-1]
                    # Remove the closing instruction tag if present
                    if "]" in ai_response:
                        ai_response = ai_response.split("]", 1)[1].strip()
                
                # Remove any system/assistant/user prefixes
                ai_response = ai_response.replace("assistant:", "")
                ai_response = ai_response.replace("system:", "")
                ai_response = ai_response.replace("user:", "")
                
                # Remove any closing tags
                ai_response = ai_response.replace("</s>", "")
                
                # Trim whitespace
                ai_response = ai_response.strip()
            
            # Save the response to the database
            AIChatMessage.objects.create(
                user=user,
                session_id=session_id,
                role="assistant",
                content=ai_response
            )
            
            return {
                "response": ai_response,
                "session_id": session_id
            }
        elif response.status_code == 503:
            # Model is loading
            logger.warning("Hugging Face model is loading. Using fallback response.")
            fallback_response = "I'm currently loading my thinking capabilities. Please try again in a moment."
            
            # Save the fallback response to the database
            AIChatMessage.objects.create(
                user=user,
                session_id=session_id,
                role="assistant",
                content=fallback_response
            )
            
            return {
                "response": fallback_response,
                "session_id": session_id,
                "error": "Model is loading"
            }
        else:
            # Handle API errors
            logger.error(f"API request failed with status code {response.status_code}: {response.text}")
            
            # Try a simpler format as fallback
            try:
                # Create a simpler prompt format
                simple_prompt = f"<s>[INST] You are an assistant for Sameer Gul's portfolio website. Answer this question: {user_message} [/INST]"
                
                simple_payload = {
                    "inputs": simple_prompt,
                    "parameters": {
                        "max_new_tokens": 200,
                        "temperature": 0.5,
                        "do_sample": True
                    }
                }
                
                # Try again with the simpler payload
                fallback_response = requests.post(
                    MODEL_URL,
                    headers=headers,
                    json=simple_payload,
                    timeout=30
                )
                
                if fallback_response.status_code == 200:
                    result = fallback_response.json()
                    
                    # Extract the response text
                    if isinstance(result, list) and len(result) > 0:
                        ai_response = result[0].get("generated_text", "")
                    else:
                        ai_response = result.get("generated_text", "")
                        
                    # Clean up the response if needed
                    if ai_response:
                        # Save the response to the database
                        AIChatMessage.objects.create(
                            user=user,
                            session_id=session_id,
                            role="assistant",
                            content=ai_response
                        )
                        
                        return {
                            "response": ai_response,
                            "session_id": session_id
                        }
            
            except Exception as inner_e:
                logger.error(f"Fallback API request failed: {str(inner_e)}")
            
            # If all else fails, use our predefined responses
            fallback_response = get_fallback_response(user_message)
            
            # Save the fallback response to the database
            AIChatMessage.objects.create(
                user=user,
                session_id=session_id,
                role="assistant",
                content=fallback_response
            )
            
            return {
                "response": fallback_response,
                "session_id": session_id
            }
    
    except requests.exceptions.Timeout:
        logger.error("API request timed out")
        fallback_response = get_fallback_response(user_message)
        
        # Save the fallback response to the database
        AIChatMessage.objects.create(
            user=user,
            session_id=session_id,
            role="assistant",
            content=fallback_response
        )
        
        return {
            "response": fallback_response,
            "session_id": session_id
        }
    
    except Exception as e:
        logger.error(f"API request failed: {str(e)}")
        fallback_response = get_fallback_response(user_message)
        
        # Save the fallback response to the database
        AIChatMessage.objects.create(
            user=user,
            session_id=session_id,
            role="assistant",
            content=fallback_response
        )
        
        return {
            "response": fallback_response,
            "session_id": session_id
        }

def generate_session_id():
    """
    Generate a unique session ID for a new chat conversation
    """
    return str(uuid.uuid4())
