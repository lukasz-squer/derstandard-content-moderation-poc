# Groq API Key Setup Guide

This application supports multiple ways to provide your Groq API key. Choose the method that works best for your use case.

## Method 1: Environment Variable (Recommended for Development)

### macOS/Linux:

```bash
# Set the environment variable
export GROQ_API_KEY="your_actual_groq_api_key_here"

# Run the application
streamlit run derstandard-demo-app.py
```

### Windows Command Prompt:

```cmd
set GROQ_API_KEY=your_actual_groq_api_key_here
streamlit run derstandard-demo-app.py
```

### Windows PowerShell:

```powershell
$env:GROQ_API_KEY="your_actual_groq_api_key_here"
streamlit run derstandard-demo-app.py
```

## Method 2: .env File (Recommended for Development)

1. Create a `.env` file in the project directory:

```bash
touch .env
```

2. Add your API key to the `.env` file:

```
GROQ_API_KEY=your_actual_groq_api_key_here
```

3. Install the required dependency:

```bash
pip install python-dotenv
```

4. Run the application:

```bash
streamlit run derstandard-demo-app.py
```

## Method 3: Streamlit Secrets (Recommended for Production/Deployment)

1. Create a `.streamlit` directory in your project:

```bash
mkdir .streamlit
```

2. Create a `secrets.toml` file:

```bash
touch .streamlit/secrets.toml
```

3. Add your API key to the secrets file:

```toml
GROQ_API_KEY = "your_actual_groq_api_key_here"
```

4. Run the application:

```bash
streamlit run derstandard-demo-app.py
```

## Method 4: Manual Input (Fallback)

If no API key is found using the above methods, the application will show an input field in the sidebar where you can enter your API key manually.

## Getting Your Groq API Key

1. Visit [https://console.groq.com/keys](https://console.groq.com/keys)
2. Sign up or log in to your account
3. Create a new API key
4. Copy the key and use it with any of the methods above

## Security Notes

- **Never commit your API keys to version control**
- Add `.env` to your `.gitignore` file
- For production deployments, use environment variables or Streamlit secrets
- The manual input method should only be used for testing

## Priority Order

The application will try to load the API key in this order:

1. Streamlit Secrets
2. Environment Variable
3. Manual Input (fallback)

If a key is found automatically, you'll see a success message and have the option to override it manually if needed.
