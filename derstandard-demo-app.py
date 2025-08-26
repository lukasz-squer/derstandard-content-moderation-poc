from PIL.Image import logger
import streamlit as st
import requests
from bs4 import BeautifulSoup
from groq import Groq
import json
from datetime import datetime
import pandas as pd
from typing import Dict, List, Tuple
import time
import os
from dotenv import load_dotenv
import logging

# Load environment variables from .env file if it exists
load_dotenv()

# ====================================
# CONFIG & SETUP
# ====================================

st.set_page_config(
    page_title="DER STANDARD - AI Moderation Demo",
    page_icon="📰",
    layout="wide"
)

# Custom CSS für DER STANDARD Look
st.markdown("""
<style>
    .main {
        padding-top: 2rem;
    }
    .stAlert {
        background-color: #f0f2f5;
        border-left: 4px solid #d41853;
    }
    h1 {
        color: #1a1a1a;
        border-bottom: 3px solid #d41853;
        padding-bottom: 10px;
    }
    .posting-box {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 5px;
        margin: 10px 0;
        border-left: 3px solid #666;
    }
    .deleted {
        border-left-color: #d41853;
        background-color: #ffe6e6;
    }
    .approved {
        border-left-color: #28a745;
        background-color: #e6ffe6;
    }
</style>
""", unsafe_allow_html=True)

# ====================================
# FORENREGELN DEFINITION
# ====================================

DEFAULT_FORUM_RULES = {
    "§1 DISKRIMINIERUNG": "Keine diskriminierenden Äußerungen bezüglich ethnischer Zugehörigkeit, Religion, Geschlecht, sexueller Orientierung, oder Behinderung.",
    "§2 BELEIDIGUNG": "Keine persönlichen Beleidigungen, Beschimpfungen oder abwertenden Äußerungen über andere User oder Personen.",
    "§3 GEWALT": "Keine Aufrufe zu Gewalt, Androhungen oder Verharmlosung von Gewalt.",
    "§4 DESINFORMATION": "Keine wissentliche Verbreitung von Falschinformationen, insbesondere bei Gesundheits- oder Sicherheitsthemen.",
    "§5 SPAM": "Kein Spam, keine Werbung, keine repetitiven Postings.",
    "§6 RELEVANZ": "Postings müssen zum Artikelthema passen. Off-Topic Diskussionen sind zu vermeiden.",
    "§7 HASSREDE": "Keine Hassrede oder extremistische Propaganda.",
    "§8 PRIVATSPHÄRE": "Keine Veröffentlichung privater Informationen anderer Personen.",
    "§9 TROLLING": "Kein absichtliches Stören der Diskussion oder Provokation.",
    "§10 RESPEKT": "Respektvoller Umgang miteinander, auch bei Meinungsverschiedenheiten."
}

def get_forum_rules():
    """Get current forum rules from session state or default"""
    if 'forum_rules' not in st.session_state:
        st.session_state.forum_rules = DEFAULT_FORUM_RULES.copy()
    return st.session_state.forum_rules

def format_rules_for_prompt():
    """Format current rules as text for LLM prompt"""
    rules = get_forum_rules()
    return "FORENREGELN DER STANDARD:\n\n" + "\n\n".join([f"{rule}: {description}" for rule, description in rules.items()])

# ====================================
# HELPER FUNCTIONS
# ====================================

@st.cache_data
def fetch_article(url: str) -> Dict[str, str]:
    """Fetcht einen DER STANDARD Artikel"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # DER STANDARD spezifische Selektoren
        title = soup.find('h1', {'class': 'article-title'}) or soup.find('h1')
        title_text = title.get_text(strip=True) if title else "Titel nicht gefunden"
        
        # Artikel-Text extrahieren
        article_body = soup.find('div', {'class': 'article-body'}) or soup.find('article')
        if article_body:
            paragraphs = article_body.find_all('p')
            content = '\n'.join([p.get_text(strip=True) for p in paragraphs[:5]])  # Erste 5 Paragraphen
        else:
            content = "Artikelinhalt konnte nicht extrahiert werden."
        
        return {
            'title': title_text,
            'content': content[:20000],  # Limitiere auf 1500 Zeichen für Demo
            'url': url,
            'success': True
        }
    except Exception as e:
        return {
            'title': 'Fehler beim Laden',
            'content': f'Artikel konnte nicht geladen werden: {str(e)}',
            'url': url,
            'success': False
        }

def analyze_posting_with_llm(
    posting: str, 
    article_title: str, 
    article_content: str,
    api_key: str,
    model: str = "llama3-8b-8192"
) -> Dict:
    """Analysiert ein Posting mit Llama via Groq"""
    
    if not api_key:
        return {
            'decision': 'ERROR',
            'confidence': 0,
            'violated_rules': [],
            'explanation': 'Bitte API Key eingeben!'
        }
    
    try:
        client = Groq(api_key=api_key)
        
        prompt = f"""Du bist ein erfahrener Foren-Moderator für DER STANDARD. Analysiere das folgende Posting nach unseren Forenregeln.

MODERATION PRINZIPIEN:
- Bevorzuge FREISCHALTEN bei Grenzfällen und Unsicherheiten
- Berücksichtige Kontext, Ironie, Sarkasmus und emotionale Reaktionen
- Lösche bei Regelverstößen
- Unterscheide zwischen konstruktiver Kritik und echten Beleidigungen

FORENREGELN:
{format_rules_for_prompt()}

ARTIKEL KONTEXT:
Titel: {article_title}
Inhalt-Auszug: {article_content[:500]}

POSTING ZU BEWERTEN:
"{posting}"

AUFGABE:
1. Entscheide: LÖSCHEN oder FREISCHALTEN
2. Bei LÖSCHEN: Welche Regel(n) wurden eindeutig und schwerwiegend verletzt?
3. Gib eine Konfidenz-Score (0-100)
4. Erkläre die Entscheidung ausführlich und begründe warum du tolerant/strikt warst
5. Die Begründung sollte kurz und auf deutsch sein.

Antworte im JSON Format:
{{
    "decision": "LÖSCHEN/FREISCHALTEN",
    "confidence": 0-100,
    "violated_rules": ["§X", "§Y"],
    "explanation": "Begründung"
}}"""

        # Log the final prompt to console
        print("="*80)
        print("FINAL PROMPT SENT TO LLM:")
        print("="*80)
        print(prompt)
        print("="*80)

        completion = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,  # Erhöht für nuanciertere, weniger strikte Antworten
            max_tokens=2000
        )
        
        response_text = completion.choices[0].message.content
        
        # Parse JSON from response
        try:
            # Extrahiere JSON aus der Antwort
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
            else:
                result = json.loads(response_text)
                
            return result
        except json.JSONDecodeError:
            # Fallback wenn JSON parsing fehlschlägt
            return {
                'decision': 'LÖSCHEN' if 'LÖSCHEN' in response_text else 'FREISCHALTEN',
                'confidence': 75,
                'violated_rules': [],
                'explanation': response_text[:200]
            }
            
    except Exception as e:
        return {
            'decision': 'ERROR',
            'confidence': 0,
            'violated_rules': [],
            'explanation': f'Fehler bei der Analyse: {str(e)}'
        }

# ====================================
# BEISPIEL-POSTINGS
# ====================================

EXAMPLE_POSTINGS = {
    "Sachliche Kritik": "Die Wirtschaftspolitik der Regierung halte ich für verfehlt, weil die Steuerreform hauptsächlich Großkonzerne begünstigt.",
    "Beleidigung": "Diese Politiker sind alle korrupte Idioten!",
    "Diskriminierung": "Ausländer nehmen uns die Jobs weg und sollten alle zurück.",
    "Konstruktiv": "Interessanter Artikel. Die Statistiken im dritten Absatz würde ich aber hinterfragen.",
    "Gewaltandrohung": "Solche Leute gehören an die Wand gestellt!",
    "Off-Topic Spam": "Besucht meine Website für günstige Kredite! www.spam.com",
    "Ironie/Grenzfall": "Na super, noch mehr gute Nachrichten... genau was wir jetzt brauchen."
}

# ====================================
# MAIN APP
# ====================================

def main():
    st.title("🤖 DER STANDARD - AI Moderation Demo")
    st.markdown("**Proof of Concept** für KI-gestützte Foren-Moderation")
    
    # Sidebar für Konfiguration
    with st.sidebar:
        st.header("⚙️ Konfiguration")
        
        # Try to get API key from multiple sources
        api_key = None
        source = ""
        
        # 1. Try Streamlit secrets (for production)
        try:
            api_key = st.secrets["GROQ_API_KEY"]
            source = "Streamlit Secrets"
        except (KeyError, FileNotFoundError):
            pass
        
        # 2. Try environment variable
        if not api_key:
            api_key = os.getenv("GROQ_API_KEY")
            if api_key:
                source = "Umgebungsvariable"
        
        # 3. Manual input as fallback
        if api_key:
            st.success(f"✅ API Key aus {source} geladen")
            # Show option to override
            if st.checkbox("API Key manuell überschreiben"):
                api_key = st.text_input(
                    "Groq API Key",
                    type="password",
                    help="Überschreibt den automatisch geladenen Key"
                )
        else:
            api_key = st.text_input(
                "Groq API Key",
                type="password",
                help="Kostenlos erhältlich auf groq.com"
            )
        
        if not api_key:
            st.info("👉 [Groq API Key hier erhalten](https://console.groq.com/keys) (kostenlos!)")
            
            with st.expander("💡 Weitere Optionen für API Key"):
                st.markdown("""
                **Umgebungsvariable** (empfohlen):
                ```bash
                export GROQ_API_KEY="your_key_here"
                ```
                
                **.env Datei**:
                ```
                GROQ_API_KEY=your_key_here
                ```
                
                **Streamlit Secrets** (für Deployment):
                Erstelle `.streamlit/secrets.toml`:
                ```toml
                GROQ_API_KEY = "your_key_here"
                ```
                """)
        
        model = st.selectbox(
            "LLM Modell",
            ["llama3-8b-8192", "llama-3.1-70b-versatile", "mixtral-8x7b-32768"],
            help="Verschiedene Modelle für Tests"
        )
        
        st.divider()
        st.header("📊 Session Statistiken")
        if 'stats' not in st.session_state:
            st.session_state.stats = {'total': 0, 'deleted': 0, 'approved': 0}
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Gelöscht", st.session_state.stats['deleted'])
        with col2:
            st.metric("Freigegeben", st.session_state.stats['approved'])
        
        if st.button("Statistiken zurücksetzen"):
            st.session_state.stats = {'total': 0, 'deleted': 0, 'approved': 0}
            st.session_state.history = []
    
    # Main Content Area
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📝 Moderation", "📊 Analyse", "📚 Regeln", "⚙️ Regeln Konfiguration", "💾 Historie"])
    
    with tab1:
        st.header("1️⃣ Artikel laden")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            article_url = st.text_input(
                "DER STANDARD Artikel URL",
                placeholder="https://www.derstandard.at/story/...",
                value="https://www.derstandard.at/story/3000000284378"
            )
        with col2:
            load_button = st.button("📥 Artikel laden", type="primary", use_container_width=True)
        
        # Artikel laden und anzeigen
        if load_button and article_url:
            with st.spinner("Lade Artikel..."):
                article_data = fetch_article(article_url)
                st.session_state.article = article_data
        
        if 'article' in st.session_state:
            article = st.session_state.article
            
            if article['success']:
                st.success("✅ Artikel erfolgreich geladen!")
                
                # Artikel-Info Box
                with st.expander("📰 **Artikel-Kontext**", expanded=True):
                    st.subheader(article['title'])
                    st.caption(f"🔗 {article['url']}")
                    st.text(article['content'])
            else:
                st.error(article['content'])
        
        # Posting Analyse Section
        st.header("2️⃣ Posting analysieren")
        
        # Beispiel-Postings Quick Select
        st.caption("**Beispiel-Postings zum Testen:**")
        example_cols = st.columns(4)
        
        # Store selected example in session state to persist across reruns
        if 'selected_example' not in st.session_state:
            st.session_state.selected_example = ""
        
        for idx, (label, text) in enumerate(EXAMPLE_POSTINGS.items()):
            with example_cols[idx % 4]:
                if st.button(label, key=f"ex_{idx}", use_container_width=True):
                    st.session_state.selected_example = text
                    st.rerun()  # Force immediate rerun to update text area
        
        # Initialize posting text in session state if not exists
        if 'posting_text_content' not in st.session_state:
            st.session_state.posting_text_content = ""
        
        # If an example was selected, update the content
        if st.session_state.selected_example:
            st.session_state.posting_text_content = st.session_state.selected_example
            st.session_state.selected_example = ""  # Reset after using
        
        # Posting Input - use session state to persist content
        posting_text = st.text_area(
            "Posting-Text eingeben",
            value=st.session_state.posting_text_content,
            height=100,
            placeholder="Geben Sie hier das zu prüfende Posting ein...",
            key="posting_text_input"
        )
        
        # Update session state with current content
        st.session_state.posting_text_content = posting_text
        
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            analyze_button = st.button(
                "🔍 Posting analysieren",
                type="primary",
                use_container_width=True,
                disabled=not api_key
            )
        with col2:
            if st.button("🗑️ Zurücksetzen", use_container_width=True):
                st.session_state.pop('last_analysis', None)
        
        with col3:
            if st.button("🧹 Text löschen", use_container_width=True):
                st.session_state.posting_text_content = ""
                st.rerun()

        # Analyse durchführen
        if analyze_button and posting_text and 'article' in st.session_state:
            with st.spinner("🤖 KI analysiert Posting..."):
                start_time = time.time()
                
                result = analyze_posting_with_llm(
                    posting_text,
                    st.session_state.article['title'],
                    st.session_state.article['content'],
                    api_key,
                    model
                )
                
                analysis_time = time.time() - start_time
                result['analysis_time'] = analysis_time
                result['posting'] = posting_text
                result['timestamp'] = datetime.now()
                
                st.session_state.last_analysis = result
                
                # Update Statistics
                st.session_state.stats['total'] += 1
                if result['decision'] == 'LÖSCHEN':
                    st.session_state.stats['deleted'] += 1
                else:
                    st.session_state.stats['approved'] += 1
                
                # Add to history
                if 'history' not in st.session_state:
                    st.session_state.history = []
                st.session_state.history.append(result)
        
        # Ergebnis anzeigen
        if 'last_analysis' in st.session_state:
            result = st.session_state.last_analysis
            
            st.divider()
            st.header("📋 Analyse-Ergebnis")
            
            # Entscheidungs-Box
            if result['decision'] == 'LÖSCHEN':
                st.error(f"🚫 **ENTSCHEIDUNG: POSTING LÖSCHEN**")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Konfidenz", f"{result.get('confidence', 0)}%")
                with col2:
                    st.metric("Analyse-Zeit", f"{result.get('analysis_time', 0):.2f}s")
                
                if result.get('violated_rules'):
                    st.warning(f"**Verletzte Regeln:** {', '.join(result['violated_rules'])}")
                
            elif result['decision'] == 'FREISCHALTEN':
                st.success(f"✅ **ENTSCHEIDUNG: POSTING FREISCHALTEN**")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Konfidenz", f"{result.get('confidence', 0)}%")
                with col2:
                    st.metric("Analyse-Zeit", f"{result.get('analysis_time', 0):.2f}s")
            else:
                st.error(f"❌ Fehler bei der Analyse")
            
            # Begründung
            with st.expander("💭 **KI-Begründung**", expanded=True):
                st.write(result.get('explanation', 'Keine Begründung verfügbar'))
            
            # Posting nochmal anzeigen
            with st.expander("📝 **Analysiertes Posting**"):
                st.text(result.get('posting', ''))
    
    with tab2:
        st.header("📊 Analyse Dashboard")
        
        if 'history' in st.session_state and st.session_state.history:
            # Statistiken
            col1, col2, col3, col4 = st.columns(4)
            
            total = len(st.session_state.history)
            deleted = sum(1 for h in st.session_state.history if h['decision'] == 'LÖSCHEN')
            approved = sum(1 for h in st.session_state.history if h['decision'] == 'FREISCHALTEN')
            avg_confidence = sum(h.get('confidence', 0) for h in st.session_state.history) / total if total > 0 else 0
            avg_time = sum(h.get('analysis_time', 0) for h in st.session_state.history) / total if total > 0 else 0
            
            with col1:
                st.metric("Gesamt", total)
            with col2:
                st.metric("Löschquote", f"{(deleted/total*100):.1f}%")
            with col3:
                st.metric("Ø Konfidenz", f"{avg_confidence:.1f}%")
            with col4:
                st.metric("Ø Zeit", f"{avg_time:.2f}s")
            
            # Violations Chart
            st.subheader("Häufigste Regelverstöße")
            violations = {}
            for h in st.session_state.history:
                for rule in h.get('violated_rules', []):
                    violations[rule] = violations.get(rule, 0) + 1
            
            if violations:
                df = pd.DataFrame(violations.items(), columns=['Regel', 'Anzahl'])
                st.bar_chart(df.set_index('Regel'))
            
            # Konfidenz-Verteilung
            st.subheader("Konfidenz-Verteilung")
            confidences = [h.get('confidence', 0) for h in st.session_state.history]
            st.line_chart(confidences)
            
        else:
            st.info("Noch keine Analysen durchgeführt. Starten Sie mit der Moderation!")
    
    with tab3:
        st.header("📚 Aktuelle Forenregeln")
        
        current_rules = get_forum_rules()
        
        for rule_name, rule_description in current_rules.items():
            st.markdown(f"**{rule_name}**: {rule_description}")
            st.markdown("")
        
        st.divider()
        st.subheader("💡 Moderations-Prinzipien")
        st.markdown("""
        - **Kontext beachten**: Aussagen immer im Artikelkontext bewerten
        - **Ironie erkennen**: Sarkasmus und Ironie richtig einordnen
        - **Grenzfälle**: Bei Unsicherheit eher freischalten
        - **Transparenz**: Entscheidungen müssen begründbar sein
        - **Konsistenz**: Gleiche Verstöße gleich behandeln
        """)
    
    with tab4:
        st.header("⚙️ Forenregeln Konfiguration")
        
        st.info("""
        **💡 Hinweise zur Regelkonfiguration:**
        
        - Änderungen an den Regeln wirken sich sofort auf zukünftige Moderationsentscheidungen aus
        - Die KI wird die aktuellen Regeln zur Bewertung von Postings verwenden
        - Sie können Regeln bearbeiten, hinzufügen, löschen oder komplett zurücksetzen
        - Export/Import ermöglicht das Sichern und Wiederherstellen von Regelsets
        """)
        
        current_rules = get_forum_rules()
        
        # Rules Management Actions
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            if st.button("🔄 Auf Standard zurücksetzen", use_container_width=True):
                st.session_state.forum_rules = DEFAULT_FORUM_RULES.copy()
                st.success("Regeln auf Standard zurückgesetzt!")
                st.rerun()
        
        with col2:
            if st.button("➕ Neue Regel hinzufügen", use_container_width=True):
                if 'adding_rule' not in st.session_state:
                    st.session_state.adding_rule = True
                else:
                    st.session_state.adding_rule = not st.session_state.adding_rule
        
        # Add New Rule Form
        if st.session_state.get('adding_rule', False):
            with st.container():
                st.subheader("➕ Neue Regel hinzufügen")
                
                col1, col2 = st.columns([1, 2])
                with col1:
                    new_rule_name = st.text_input(
                        "Regel-Name (z.B. '§11 BEISPIEL')",
                        placeholder="§11 NEUE_REGEL",
                        key="new_rule_name"
                    )
                
                with col2:
                    new_rule_description = st.text_area(
                        "Regel-Beschreibung",
                        placeholder="Beschreibung der neuen Regel...",
                        key="new_rule_description",
                        height=100
                    )
                
                col1, col2 = st.columns([1, 1])
                with col1:
                    if st.button("✅ Regel hinzufügen", use_container_width=True):
                        if new_rule_name and new_rule_description:
                            st.session_state.forum_rules[new_rule_name] = new_rule_description
                            st.session_state.adding_rule = False
                            st.success(f"Regel '{new_rule_name}' hinzugefügt!")
                            st.rerun()
                        else:
                            st.error("Bitte beide Felder ausfüllen!")
                
                with col2:
                    if st.button("❌ Abbrechen", use_container_width=True):
                        st.session_state.adding_rule = False
                        st.rerun()
                
                st.divider()
        
        # Export/Import functionality
        st.subheader("💾 Import/Export")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Export rules as JSON
            rules_json = json.dumps(current_rules, indent=2, ensure_ascii=False)
            st.download_button(
                label="📥 Regeln als JSON exportieren",
                data=rules_json,
                file_name=f"forum_rules_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True
            )
        
        with col2:
            # Import rules
            uploaded_file = st.file_uploader(
                "📤 Regeln aus JSON importieren",
                type=['json'],
                help="Laden Sie eine JSON-Datei mit Forenregeln hoch"
            )
            
            if uploaded_file is not None:
                try:
                    imported_rules = json.load(uploaded_file)
                    if isinstance(imported_rules, dict):
                        st.session_state.forum_rules = imported_rules
                        st.success("Regeln erfolgreich importiert!")
                        st.rerun()
                    else:
                        st.error("Ungültiges JSON-Format!")
                except json.JSONDecodeError:
                    st.error("Fehler beim Lesen der JSON-Datei!")
        
        st.divider()
        
        # Preview how rules will look in LLM prompt
        st.subheader("👁️ Vorschau für KI-Prompt")
        with st.expander("Zeige, wie die Regeln der KI präsentiert werden"):
            st.code(format_rules_for_prompt(), language="text")
        
        st.divider()
        
        # Edit existing rules
        st.subheader("✏️ Regeln bearbeiten")
        
        # Create tabs for each rule for better organization
        if current_rules:
            rule_tabs = st.tabs([f"Regel {i+1}" for i in range(len(current_rules))])
            
            for idx, (rule_name, rule_description) in enumerate(current_rules.items()):
                with rule_tabs[idx]:
                    st.markdown(f"**{rule_name}**")
                    
                    # Edit rule name
                    new_name = st.text_input(
                        "Regel-Name:",
                        value=rule_name,
                        key=f"rule_name_{idx}"
                    )
                    
                    # Edit rule description
                    new_description = st.text_area(
                        "Regel-Beschreibung:",
                        value=rule_description,
                        height=100,
                        key=f"rule_desc_{idx}"
                    )
                    
                    col1, col2, col3 = st.columns([1, 1, 1])
                    
                    with col1:
                        if st.button(f"💾 Speichern", key=f"save_{idx}", use_container_width=True):
                            if new_name and new_description:
                                # Remove old rule and add updated one
                                updated_rules = {}
                                for i, (old_name, old_desc) in enumerate(current_rules.items()):
                                    if i == idx:
                                        updated_rules[new_name] = new_description
                                    else:
                                        updated_rules[old_name] = old_desc
                                
                                st.session_state.forum_rules = updated_rules
                                st.success("Regel gespeichert!")
                                st.rerun()
                            else:
                                st.error("Name und Beschreibung dürfen nicht leer sein!")
                    
                    with col2:
                        if st.button(f"🔄 Zurücksetzen", key=f"reset_{idx}", use_container_width=True):
                            # Reset to original values
                            st.rerun()
                    
                    with col3:
                        if st.button(f"🗑️ Löschen", key=f"delete_{idx}", use_container_width=True):
                            # Confirm deletion
                            if f'confirm_delete_{idx}' not in st.session_state:
                                st.session_state[f'confirm_delete_{idx}'] = True
                                st.warning("Noch einmal klicken zum Bestätigen!")
                            else:
                                # Delete the rule
                                updated_rules = {k: v for i, (k, v) in enumerate(current_rules.items()) if i != idx}
                                st.session_state.forum_rules = updated_rules
                                del st.session_state[f'confirm_delete_{idx}']
                                st.success("Regel gelöscht!")
                                st.rerun()
        
        else:
            st.info("Keine Regeln vorhanden. Fügen Sie eine neue Regel hinzu oder setzen Sie auf Standard zurück.")
    
    with tab5:
        st.header("💾 Analyse-Historie")
        
        if 'history' in st.session_state and st.session_state.history:
            # Export Button
            if st.button("📥 Historie als JSON exportieren"):
                history_json = json.dumps(
                    [
                        {
                            'posting': h['posting'],
                            'decision': h['decision'],
                            'confidence': h.get('confidence'),
                            'violated_rules': h.get('violated_rules'),
                            'explanation': h.get('explanation'),
                            'timestamp': h.get('timestamp').isoformat() if h.get('timestamp') else None
                        }
                        for h in st.session_state.history
                    ],
                    indent=2,
                    ensure_ascii=False
                )
                st.download_button(
                    label="Download JSON",
                    data=history_json,
                    file_name=f"moderation_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
            
            # Historie-Tabelle
            for idx, item in enumerate(reversed(st.session_state.history)):
                with st.expander(
                    f"{'🚫' if item['decision'] == 'LÖSCHEN' else '✅'} "
                    f"Posting {len(st.session_state.history) - idx}: "
                    f"{item['posting'][:50]}..."
                ):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Entscheidung:** {item['decision']}")
                        st.write(f"**Konfidenz:** {item.get('confidence', 'N/A')}%")
                    with col2:
                        if item.get('violated_rules'):
                            st.write(f"**Regeln:** {', '.join(item['violated_rules'])}")
                        if item.get('timestamp'):
                            st.write(f"**Zeit:** {item['timestamp'].strftime('%H:%M:%S')}")
                    
                    st.write("**Begründung:**")
                    st.text(item.get('explanation', 'Keine Begründung'))
        else:
            st.info("Noch keine Historie vorhanden.")

if __name__ == "__main__":
    main()