import gradio as gr
from src.scraper import ElectionScraper
from src.sentiment import SentimentAnalyzer
from src.predictor import ElectionPredictor
from src.candidate_db import CandidateDB
from src.constituency import ConstituencyData
import pandas as pd
import json
import os
import sys # Needed for path manipulation if utils is not found automatically

# --- Path Correction for utils.py if needed ---
# This block ensures `src` is in the Python path so `utils` can be imported.
# It's good practice if your file structure might vary or when running in certain environments.
try:
    # Check if src is already in path (e.g., if running from parent directory)
    import src.utils
except ImportError:
    print("Attempting to add 'src' to sys.path for imports.")
    current_dir = os.path.dirname(__file__)
    # Assuming src is a subdirectory of the current directory
    if os.path.exists(os.path.join(current_dir, 'src')):
        sys.path.insert(0, current_dir)
    else:
        # Fallback: try one level up if project root is not where app.py is directly
        parent_dir = os.path.dirname(current_dir)
        if os.path.exists(os.path.join(parent_dir, 'src')):
            sys.path.insert(0, parent_dir)
        else:
            print("Could not automatically find 'src' directory. Please ensure it's accessible.")


# --- Initialization ---
# Initialize data management modules
# These will create json files if they don't exist thanks to load_data() logic
candidate_db = CandidateDB(file_path="data/candidates.json")
constituency_db = ConstituencyData(file_path="data/constituencies.json")

# Initialize core modules
scraper = ElectionScraper()
sentiment_analyzer = SentimentAnalyzer()
predictor = ElectionPredictor()

# --- Helper Functions ---

def update_db_files():
    """Saves current state of DBs to their respective JSON files."""
    candidate_db.save_data()
    constituency_db.save_data()
    return "Database files saved successfully."

# --- Gradio Interface Components ---

def create_prediction_tab():
    with gr.Blocks() as prediction_tab:
        gr.Markdown("# Election Prediction based on Text Analysis")
        gr.Markdown("Analyze news articles, social media posts, or any text to gauge sentiment and predict relevance to candidates/parties.")

        with gr.Row():
            text_input = gr.Textbox(label="Enter Text for Analysis", lines=5, placeholder="Paste news headlines, political commentary, social media posts here...")
            
            # Dynamically populate candidates list from DB
            candidates_list_str = gr.Textbox(label="Candidates/Parties (comma-separated)", 
                                            value=",".join(candidate_db.get_all_candidate_names()), 
                                            placeholder="e.g., M. K. Stalin, AIADMK, BJP")

        with gr.Row():
            num_preds_slider = gr.Slider(minimum=1, maximum=10, step=1, value=5, label="Number of Top Predictions")
            analyze_btn = gr.Button("Analyze Text & Predict")

        with gr.Accordion("Detailed Analysis Results", open=False):
            with gr.Tabs():
                with gr.TabItem("Sentiment Analysis"):
                    sentiment_output = gr.JSON(label="Sentiment Analysis Result")
                with gr.TabItem("Candidate/Party Relevance"):
                    prediction_output = gr.JSON(label="Candidate/Party Prediction Scores")
                with gr.TabItem("Scraped News Articles (if applicable)"):
                    scraped_news_output = gr.JSON(label="Related News Articles")

        gr.Markdown("---")
        gr.Markdown("### Example Usage")
        gr.Examples(
            examples=[
                ["Chennai: The ruling DMK party held a massive rally today in Madurai, with Chief Minister M. K. Stalin addressing thousands of supporters. He spoke about the government's achievements in welfare schemes and criticized the opposition AIADMK for their performance. BJP leader K. Annamalai was in Coimbatore, meeting with party workers.", "M. K. Stalin, DMK, AIADMK, BJP, Kamal Haasan, MNM"],
                ["The central government's new economic policy is facing criticism from various state leaders. The focus on industrial growth is seen as neglecting agricultural sector needs, which is a major concern for many in Tamil Nadu.", "DMK, AIADMK, BJP, Congress"]
            ],
            inputs=[text_input, candidates_list_str]
        )

        def perform_analysis(text, candidates_str, num_preds):
            if not text.strip():
                return {"label": "Neutral", "score": 0.0, "warning": "No text provided for analysis."}, [], []
            
            candidate_list = [c.strip() for c in candidates_str.split(',') if c.strip()]
            if not candidate_list:
                 return {"label": "Neutral", "score": 0.0, "warning": "No candidates/parties provided for prediction."}, [], []

            # Sentiment Analysis
            sentiment = sentiment_analyzer.analyze(text)

            # Prediction
            predictions = predictor.predict(text, candidate_list, num_predictions=int(num_preds))

            # Basic scrape for news if input looks like a query
            scraped_news = []
            # Heuristic for when to scrape: input is reasonably long and contains keywords
            if len(text.split()) > 7 and any(word in text.lower() for word in ["election", "politics", "candidate", "party", "rally", "vote", "government", "policy", "leaders"]):
                query_text = text[:100] # Use first 100 chars as a hint for query
                scraped_news = scraper.scrape_news_articles(query=f"Tamil Nadu Politics {query_text}", num_articles=3) 
                if not scraped_news:
                    scraped_news = [{"title": "No relevant news found via scraping.", "url": "#", "source": "N/A", "query": "N/A"}]
            else:
                 scraped_news = [{"title": "Input too short or lacks keywords for news scraping.", "url": "#", "source": "N/A", "query": "N/A"}]


            return sentiment, predictions, scraped_news
        
        analyze_btn.click(
            perform_analysis,
            inputs=[text_input, candidates_list_str, num_preds_slider],
            outputs=[sentiment_output, prediction_output, scraped_news_output]
        )
    return prediction_tab

def create_data_management_tab():
    with gr.Blocks() as data_management_tab:
        gr.Markdown("# Data Management")
        gr.Markdown("Manage candidate and constituency data. Changes will be saved to local JSON files.")

        # Stores the index of the currently selected row in the DataFrame
        # This helps in updating/removing the correct item.
        selected_candidate_index = gr.State(None)
        selected_constituency_index = gr.State(None)

        with gr.Tabs():
            with gr.TabItem("Candidate Management"):
                gr.Markdown("## Candidates")
                with gr.Row():
                    with gr.Column():
                        name_input = gr.Textbox(label="Candidate Name")
                        party_input = gr.Textbox(label="Party")
                        constituency_input = gr.Textbox(label="Constituency")
                        status_input = gr.Textbox(label="Status", value="Active")
                        activity_input = gr.Textbox(label="Recent Activity", lines=2)
                        add_candidate_btn = gr.Button("Add Candidate")
                        update_candidate_btn = gr.Button("Update Selected Candidate")
                        remove_candidate_btn = gr.Button("Remove Selected Candidate")
                        
                        # Message output for feedback
                        candidate_msg_output = gr.Textbox(label="Status Message", interactive=False, lines=1)

                    with gr.Column():
                        candidate_data_output = gr.DataFrame(
                            headers=["name", "party", "constituency", "status", "recent_activity"],
                            row_count=(10, "dynamic"), # Set a default row count, dynamic means it can grow
                            datatype=["str", "str", "str", "str", "str"],
                            label="Current Candidates",
                            interactive=True # Allows editing within the DataFrame cells
                        )

                def add_candidate_handler(name, party, constituency, status, activity):
                    msg = ""
                    if not all([name, party, constituency]):
                        msg = "Error: Name, Party, and Constituency are required."
                    elif candidate_db.add_candidate(name, party, constituency, status, activity):
                        msg = "Candidate added successfully."
                        # Clear input fields after successful addition
                        return msg, "", "", "", "", "" 
                    else:
                        msg = f"Failed to add candidate '{name}' (possibly already exists or invalid input)."
                    
                    return msg, name, party, constituency, status, activity # Return current values on error

                def update_selected_candidate_handler(data, selected_idx, name, party, constituency, status, activity):
                    msg = ""
                    if selected_idx is None:
                        msg = "Please select a candidate row to update."
                        return msg, name, party, constituency, status, activity
                    
                    if not all([name, party, constituency]):
                        msg = "Error: Name, Party, and Constituency cannot be empty for update."
                        return msg, name, party, constituency, status, activity

                    if candidate_db.update_candidate_status_and_activity(name, status, activity):
                        msg = f"Candidate '{name}' updated."
                        # Update the DataFrame and clear/reset the state
                        return msg, name, party, constituency, status, activity # Keep fields populated upon success
                    else:
                         # Assume update_candidate_status_and_activity handles 'not found' internally and prints msg
                        msg = f"Failed to update candidate '{name}'. Check console log."
                        return msg, name, party, constituency, status, activity

                def remove_selected_candidate_handler(data, selected_idx):
                    msg = ""
                    if selected_idx is None or not data:
                        msg = "Please select a candidate row to remove."
                        return msg, None
                     
                    name_to_remove = data[selected_idx]['name'] # Get name from selected row data
                    if candidate_db.remove_candidate(name_to_remove):
                        msg = f"Candidate '{name_to_remove}' removed."
                        # Reset state and clear inputs after successful removal
                        return msg, None # None for selected index
                    else:
                        msg = f"Failed to remove candidate '{name_to_remove}' (not found)."
                        return msg, selected_idx

                def update_candidate_dataframe():
                    candidates = candidate_db.get_all_candidates()
                    return pd.DataFrame(candidates) if candidates else pd.DataFrame(columns=["name", "party", "constituency", "status", "recent_activity"])

                def handle_candidate_row_select(evt: gr.SelectData):
                    # evt.index is the row index that was clicked
                    df_data = update_candidate_dataframe().to_dict('records') # Get data as a list of dicts
                    if evt.index < len(df_data):
                        row = df_data[evt.index]
                        # Populate input fields with selected row data
                        return row.get('name', ''), row.get('party', ''), row.get('constituency', ''), row.get('status', 'Active'), row.get('recent_activity', ''), evt.index
                    return "", "", "", "", "", None # Clear inputs and state if selection is invalid


                # -- Event Listeners for Candidate Management --
                add_candidate_btn.click(
                    fn=add_candidate_handler,
                    inputs=[name_input, party_input, constituency_input, status_input, activity_input],
                    outputs=[candidate_msg_output, name_input, party_input, constituency_input, status_input, activity_input]
                ).then(
                    fn=update_candidate_dataframe, outputs=candidate_data_output # Refresh DataFrame
                )

                # When a row is selected, populate the input fields and store the index in state
                candidate_data_output.select(
                    fn=handle_candidate_row_select,
                    inputs=[], # No inputs needed for select event itself
                    outputs=[name_input, party_input, constituency_input, status_input, activity_input, selected_candidate_index] # Output to input fields and state
                )
                
                # Update button uses the stored index from gr.State()
                update_candidate_btn.click(
                    fn=update_selected_candidate_handler,
                    inputs=[candidate_data_output, selected_candidate_index, name_input, party_input, constituency_input, status_input, activity_input],
                    outputs=[candidate_msg_output, name_input, party_input, constituency_input, status_input, activity_input]
                ).then(
                    fn=update_candidate_dataframe, outputs=candidate_data_output # Refresh DataFrame
                )
                
                # Remove button uses the stored index from gr.State()
                remove_candidate_btn.click(
                    fn=remove_selected_candidate_handler,
                    inputs=[candidate_data_output, selected_candidate_index],
                    outputs=[candidate_msg_output, selected_candidate_index] # Clear msg, reset state
                ).then(
                    fn=update_candidate_dataframe, outputs=candidate_data_output # Refresh DataFrame
                )

                # Initial load of candidate data into DataFrame
                candidate_data_output.value = update_candidate_dataframe()

            with gr.TabItem("Constituency Management"):
                gr.Markdown("## Constituencies")
                with gr.Row():
                    with gr.Column():
                        const_name_input = gr.Textbox(label="Constituency Name")
                        district_input = gr.Textbox(label="District")
                        parties_input = gr.Textbox(label="Key Parties (comma-separated)", placeholder="e.g., DMK,AIADMK,BJP")
                        mla_input = gr.Textbox(label="Incumbent MLA", placeholder="e.g., M. K. Stalin (DMK)")
                        issues_input = gr.Textbox(label="Major Issues (comma-separated)", placeholder="e.g., Water,Roads,Jobs")
                        add_constituency_btn = gr.Button("Add Constituency")
                        update_constituency_btn = gr.Button("Update Selected Constituency")
                        remove_constituency_btn = gr.Button("Remove Selected Constituency")
                        
                        const_msg_output = gr.Textbox(label="Status Message", interactive=False, lines=1)

                    with gr.Column():
                        constituency_data_output = gr.DataFrame(
                            headers=["name", "district", "key_parties", "incumbent_mla", "major_issues"],
                            row_count=(10, "dynamic"),
                            datatype=["str", "str", "str", "str", "str"],
                            label="Current Constituencies",
                            interactive=True
                        )
                
                def constituency_to_str_lists(constituency_data):
                    """Helper to convert list values to comma-separated strings for display."""
                    if constituency_data:
                        for item in constituency_data:
                            if isinstance(item.get('key_parties'), list):
                                item['key_parties'] = ", ".join(item['key_parties'])
                            if isinstance(item.get('major_issues'), list):
                                item['major_issues'] = ", ".join(item['major_issues'])
                    return constituency_data

                def add_constituency_handler(name, district, parties_str, mla, issues_str):
                    msg = ""
                    if not name or not district:
                        msg = "Error: Constituency Name and District are required."
                        return msg, name, district, parties_str, mla, issues_str
                    
                    key_parties = [p.strip() for p in parties_str.split(',') if p.strip()]
                    major_issues = [i.strip() for i in issues_str.split(',') if i.strip()]
                    
                    if constituency_db.add_constituency(name, district, key_parties, mla, major_issues):
                        msg = "Constituency added successfully."
                        return msg, "", "", "", "", "" # Clear inputs
                    else:
                        msg = f"Failed to add constituency '{name}' (possibly already exists)."
                        return msg, name, district, parties_str, mla, issues_str

                def update_selected_constituency_handler(data, selected_idx, name, district, parties_str, mla, issues_str):
                    msg = ""
                    if selected_idx is None:
                        msg = "Please select a constituency row to update."
                        return msg, name, district, parties_str, mla, issues_str
                    
                    if not name or not district:
                        msg = "Error: Constituency Name and District cannot be empty for update."
                        return msg, name, district, parties_str, mla, issues_str

                    key_parties = [p.strip() for p in parties_str.split(',') if p.strip()]
                    major_issues = [i.strip() for i in issues_str.split(',') if i.strip()]
                    
                    if constituency_db.update_constituency(name, district, key_parties, mla, major_issues):
                        msg = f"Constituency '{name}' updated."
                        return msg, name, district, parties_str, mla, issues_str # Keep fields populated
                    else:
                        msg = f"Failed to update constituency '{name}'. Check console log."
                        return msg, name, district, parties_str, mla, issues_str
                
                def remove_selected_constituency_handler(data, selected_idx):
                    msg = ""
                    if selected_idx is None or not data:
                        msg = "Please select a constituency row to remove."
                        return msg, None
                    
                    name_to_remove = data[selected_idx]['name']
                    if constituency_db.remove_constituency(name_to_remove):
                        msg = f"Constituency '{name_to_remove}' removed."
                        return msg, None # Clear message, reset state
                    else:
                        msg = f"Failed to remove constituency '{name_to_remove}' (not found)."
                        return msg, selected_idx

                def update_constituency_dataframe():
                    constituencies = constituency_db.get_all_constituencies()
                    processed_data = constituency_to_str_lists(constituencies)
                    return pd.DataFrame(processed_data) if processed_data else pd.DataFrame(columns=["name", "district", "key_parties", "incumbent_mla", "major_issues"])

                def handle_constituency_row_select(evt: gr.SelectData):
                    df_data = update_constituency_dataframe().to_dict('records')
                    if evt.index < len(df_data):
                        row = df_data[evt.index]
                        # Populate input fields
                        return row.get('name', ''), row.get('district', ''), row.get('key_parties', ''), row.get('incumbent_mla', ''), row.get('major_issues', ''), evt.index
                    return "", "", "", "", "", None

                # -- Event Listeners for Constituency Management --
                add_constituency_btn.click(
                    add_constituency_handler,
                    inputs=[const_name_input, district_input, parties_input, mla_input, issues_input],
                    outputs=[const_msg_output, const_name_input, district_input, parties_input, mla_input, issues_input]
                ).then(
                    fn=update_constituency_dataframe, outputs=constituency_data_output
                )

                constituency_data_output.select(
                    handle_constituency_row_select,
                    inputs=[],
                    outputs=[const_name_input, district_input, parties_input, mla_input, issues_input, selected_constituency_index]
                )

                update_constituency_btn.click(
                    update_selected_constituency_handler,
                    inputs=[constituency_data_output, selected_constituency_index, const_name_input, district_input, parties_input, mla_input, issues_input],
                    outputs=[const_msg_output, const_name_input, district_input, parties_input, mla_input, issues_input]
                ).then(
                    fn=update_constituency_dataframe, outputs=constituency_data_output
                )

                remove_constituency_btn.click(
                    remove_selected_constituency_handler,
                    inputs=[constituency_data_output, selected_constituency_index],
                    outputs=[const_msg_output, selected_constituency_index]
                ).then(
                    fn=update_constituency_dataframe, outputs=constituency_data_output
                )
                
                # Initial load of constituency data
                constituency_data_output.value = update_constituency_dataframe()

        save_btn = gr.Button("Save All Database Changes")
        save_status_msg = gr.Textbox(label="Save Status", interactive=False, lines=1)
        save_btn.click(update_db_files, outputs=save_status_msg)

    return data_management_tab

def create_scraper_tab():
    with gr.Blocks() as scraper_tab:
        gr.Markdown("# Web Scraper")
        gr.Markdown("Fetch raw HTML content from a given URL or scrape news articles.")

        with gr.Tabs():
            with gr.TabItem("Custom URL Scraper"):
                url_input_custom = gr.Textbox(label="Enter URL to scrape", placeholder="e.g., https://example.com")
                scrape_btn_custom = gr.Button("Scrape URL")
                scraped_html_output = gr.Textbox(label="Scraped HTML Content", lines=15, interactive=False)
                scrape_error_output_custom = gr.Textbox(label="Scraping Status/Errors", interactive=False)

                def perform_scrape_custom(url):
                    if not url.strip():
                        return "", "Please enter a URL."
                    
                    content = scraper.scrape_custom_url(url)
                    if "Failed to retrieve content" in content:
                        return "", content # Return empty content and the error message
                    else:
                        return content, f"Successfully scraped {url}"

                scrape_btn_custom.click(
                    perform_scrape_custom,
                    inputs=url_input_custom,
                    outputs=[scraped_html_output, scrape_error_output_custom]
                )

            with gr.TabItem("News Article Scraper"):
                query_news_input = gr.Textbox(label="News Query (e.g., 'Tamil Nadu election')", placeholder="Enter your search query")
                num_articles_slider = gr.Slider(minimum=1, maximum=20, step=1, value=5, label="Number of Articles to Fetch")
                scrape_news_btn = gr.Button("Scrape News")
                scraped_news_output = gr.JSON(label="Scraped News Articles")
                scrape_error_output_news = gr.Textbox(label="Scraping Status/Errors", interactive=False)

                def perform_scrape_news(query, num_articles):
                    if not query.strip():
                        return [], "Please enter a news query."
                    
                    news_items = scraper.scrape_news_articles(query=query, num_articles=int(num_articles))
                    if not news_items:
                        return [], f"No news found for query: '{query}'"
                    else:
                        return news_items, f"Successfully scraped {len(news_items)} articles for '{query}'."

                scrape_news_btn.click(
                    perform_scrape_news,
                    inputs=[query_news_input, num_articles_slider],
                    outputs=[scraped_news_output, scrape_error_output_news]
                )
    return scraper_tab

def create_about_tab():
    with gr.Blocks() as about_tab:
        gr.Markdown("# About TN Election Predictor")
        gr.Markdown(
            """
            This application provides tools for analyzing political data related to Tamil Nadu elections.

            **Features:**
            *   **Prediction & Analysis:** Perform sentiment analysis and predict candidate/party relevance based on text input.
            *   **Web Scraper:** Fetch raw HTML content from specified URLs or scrape news articles.
            *   **Data Management:** Manage a local database of candidates and constituencies, which are saved to JSON files.
            *   **Information about Constituencies:** View details for various constituencies in Tamil Nadu.

            **Models Used:**
            *   Sentiment Analysis: `cardiffnlp/twitter-roberta-base-sentiment-latest` (Transformers) - **Actual Model Loading**
            *   Zero-Shot Classification (Prediction): `facebook/bart-large-mnli` (Transformers) - **Actual Model Loading**

            **Data Sources:**
            *   Candidate and Constituency data is managed locally and can be updated via the 'Data Management' tab.
            *   News articles are scraped from Google News (with limitations).

            **Note:** This application uses placeholder data initially and basic scraping. Real-world election prediction requires more sophisticated data sourcing, advanced NLP techniques, and careful handling of data privacy and ethical considerations.
            """
        )
        gr.Markdown("---")
        gr.Markdown("### Project Structure")
        gr.Markdown(
            """
            - `app.py`: Main Gradio application.
            - `requirements.txt`: Project dependencies.
            - `static/styles.css`: Custom styling for Gradio.
            - `src/`: Directory containing all source modules:
                - `utils.py`: Utility functions.
                - `scraper.py`: Web scraping functionality.
                - `sentiment.py`: Sentiment analysis module.
                - `predictor.py`: Election prediction module.
                - `candidate_db.py`: Candidate data management.
                - `constituency.py`: Constituency data management.
            - `data/`: Directory for storing JSON database files (`candidates.json`, `constituencies.json`).
            """
        )
        gr.Markdown("---")
        gr.Markdown("### Important Notes regarding Hugging Face Models")
        gr.Markdown(
            """
            The first time this application runs, it will download the pre-trained models from Hugging Face. This can take a considerable amount of time and disk space.
            - **Sentiment Model**: `cardiffnlp/twitter-roberta-base-sentiment-latest`
            - **Prediction Model**: `facebook/bart-large-mnli`
            Ensure you have enough disk space and a stable internet connection for the initial load. The model loading warnings (`UNEXPECTED`) during startup are generally ignorable.
            """
        )
    return about_tab

# --- Gradio Interface Setup ---
# --- IMPORTANT: Gradio 6.0+ requires passing CSS to launch() ---
# css_file = "static/styles.css" # Define CSS file path

with gr.Blocks() as demo: # Removed css parameter from Blocks
    gr.Markdown("# Tamil Nadu Election Predictor Dashboard")
    
    with gr.Tabs():
        with gr.TabItem("Prediction & Analysis"):
            demo.add(create_prediction_tab())
        with gr.TabItem("Data Management"):
            demo.add(create_data_management_tab())
        with gr.TabItem("Web Scraper"):
            demo.add(create_scraper_tab())
        with gr.TabItem("About"):
            demo.add(create_about_tab())

if __name__ == "__main__":
    # Ensure data directory exists
    if not os.path.exists("data"):
        os.makedirs("data")
        print("Created 'data' directory.")

    # The DB loading logic in __init__ already handles file creation/population
    # We just need to ensure they are initialized.
    print("Initializing data managers...")
    cand_db_instance = CandidateDB(file_path="data/candidates.json")
    const_db_instance = ConstituencyData(file_path="data/constituencies.json")
    print("Data managers initialized.")

    print("Starting Gradio interface...")
    demo.launch(server_name="0.0.0.0", server_port=7860, css="static/styles.css")
