import gradio as gr
from src.scraper import ElectionScraper
from src.sentiment import SentimentAnalyzer
from src.predictor import ElectionPredictor
from src.candidate_db import CandidateDB
from src.constituency import ConstituencyData
import pandas as pd
import json
import os

# --- Initialization ---
if not os.path.exists("data"):
    os.makedirs("data")

candidate_db = CandidateDB(file_path="data/candidates.json")
constituency_db = ConstituencyData(file_path="data/constituencies.json")

scraper = ElectionScraper()
sentiment_analyzer = SentimentAnalyzer()
predictor = ElectionPredictor()

def update_db_files():
    candidate_db.save_data()
    constituency_db.save_data()
    return "Database files saved successfully."

def create_prediction_tab():
    with gr.Blocks() as prediction_tab:
        gr.Markdown("# Election Prediction based on Text Analysis")
        gr.Markdown("Analyze news articles, social media posts, or any text to gauge sentiment and predict relevance to candidates/parties.")

        with gr.Row():
            text_input = gr.Textbox(label="Enter Text for Analysis", lines=5, placeholder="Paste news headlines, political commentary, social media posts here...")
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
                ["The ruling DMK party held a massive rally today in Madurai, with Chief Minister M. K. Stalin addressing thousands. He spoke about achievements and criticized the opposition AIADMK. BJP leader K. Annamalai was in Coimbatore discussing strategies.", "M. K. Stalin, DMK, AIADMK, BJP, Kamala Haasan, MNM"],
                ["New policy faces criticism from state leaders. Focus on industrial growth seen as neglecting agriculture, a major concern in Tamil Nadu.", "DMK, AIADMK, BJP, Congress"]
            ],
            inputs=[text_input, candidates_list_str]
        )

        def perform_analysis(text, candidates_str, num_preds):
            if not text.strip():
                return {"label": "Neutral", "score": 0.0, "warning": "No text provided for analysis."}, [], []
            candidate_list = [c.strip() for c in candidates_str.split(',') if c.strip()]
            if not candidate_list:
                return {"label": "Neutral", "score": 0.0, "warning": "No candidates/parties provided for prediction."}, [], []

            sentiment = sentiment_analyzer.analyze(text)
            predictions = predictor.predict(text, candidate_list, num_predictions=int(num_preds))
            scraped_news = []
            if len(text.split()) > 5 and any(word in text.lower() for word in ["election", "politics", "candidate", "party", "rally", "vote"]):
                query_text = text[:100]
                scraped_news = scraper.scrape_news_articles(query=f"Tamil Nadu {query_text}", num_articles=3)
                if not scraped_news:
                    scraped_news = [{"title": "No relevant news found via scraping.", "url": "#", "source": "N/A", "query": "N/A"}]

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
                    with gr.Column():
                        candidate_data_output = gr.DataFrame(
                            headers=["name", "party", "constituency", "status", "recent_activity"],
                            interactive=True,
                            label="Current Candidates"
                        )

                def add_candidate_handler(name, party, constituency, status, activity):
                    if candidate_db.add_candidate(name, party, constituency, status, activity):
                        update_data_display()
                        return "Candidate added successfully.", "", "", "", "", ""
                    else:
                        return "Failed to add candidate (name might already exist or fields missing).", name, party, constituency, status, activity

                def update_selected_candidate_handler(data, selected_row_index):
                    if selected_row_index is None or not data:
                        return "Please select a candidate row to update.", "", "", "", "", ""
                    selected_candidate = data[selected_row_index]
                    name = selected_candidate['name']
                    party = selected_candidate['party']
                    constituency = selected_candidate['constituency']
                    status = selected_candidate['status']
                    activity = selected_candidate['recent_activity']
                    if candidate_db.update_candidate_status_and_activity(name, status, activity):
                        update_data_display()
                        return f"Candidate '{name}' updated.", "", "", "", "", ""
                    else:
                        return f"Failed to update candidate '{name}'.", name, party, constituency, status, activity

                def remove_selected_candidate_handler(data, selected_row_index):
                    if selected_row_index is None or not data:
                        return "Please select a candidate row to remove.", None
                    selected_candidate = data[selected_row_index]
                    name_to_remove = selected_candidate['name']
                    if candidate_db.remove_candidate(name_to_remove):
                        update_data_display()
                        return f"Candidate '{name_to_remove}' removed.", None
                    else:
                        return f"Failed to remove candidate '{name_to_remove}'.", selected_row_index

                def update_data_display():
                    candidates = candidate_db.get_all_candidates()
                    return pd.DataFrame(candidates)

                def handle_row_select(evt: gr.SelectData):
                    selected_candidate_data = candidate_db.get_all_candidates()
                    if evt.index < len(selected_candidate_data):
                        row = selected_candidate_data[evt.index]
                        return row['name'], row['party'], row['constituency'], row['status'], row['recent_activity'], evt.index
                    return "", "", "", "", "", None

                add_candidate_btn.click(
                    add_candidate_handler,
                    inputs=[name_input, party_input, constituency_input, status_input, activity_input],
                    outputs=[gr.update(value=""), name_input, party_input, constituency_input, status_input, activity_input]
                ).then(update_data_display, outputs=candidate_data_output)

                candidate_data_output.select(handle_row_select, inputs=None, outputs=[name_input, party_input, constituency_input, status_input, activity_input, gr.State()])

                update_candidate_btn.click(
                    update_selected_candidate_handler,
                    inputs=[candidate_data_output, gr.State()],
                    outputs=[gr.update(value=""), name_input, party_input, constituency_input, status_input, activity_input]
                ).then(update_data_display, outputs=candidate_data_output)

                remove_candidate_btn.click(
                    remove_selected_candidate_handler,
                    inputs=[candidate_data_output, gr.State()],
                    outputs=[gr.update(value=""), gr.State()]
                ).then(update_data_display, outputs=candidate_data_output)

                candidate_data_output.value = update_data_display()

            with gr.TabItem("Constituency Management"):
                gr.Markdown("## Constituencies")
                with gr.Row():
                    with gr.Column():
                        const_name_input = gr.Textbox(label="Constituency Name")
                        district_input = gr.Textbox(label="District")
                        parties_input = gr.Textbox(label="Key Parties (comma-separated)", placeholder="e.g., DMK,AIADMK,BJP")
                        mla_input = gr.Textbox(label="Incumbent MLA")
                        issues_input = gr.Textbox(label="Major Issues (comma-separated)", placeholder="e.g., Water,Roads")
                        add_constituency_btn = gr.Button("Add Constituency")
                        update_constituency_btn = gr.Button("Update Selected Constituency")
                        remove_constituency_btn = gr.Button("Remove Selected Constituency")
                    with gr.Column():
                        constituency_data_output = gr.DataFrame(
                            headers=["name", "district", "key_parties", "incumbent_mla", "major_issues"],
                            interactive=True,
                            label="Current Constituencies"
                        )

                def constituency_to_str_lists(constituency_data):
                    if constituency_data:
                        for item in constituency_data:
                            if isinstance(item.get('key_parties'), list):
                                item['key_parties'] = ", ".join(item['key_parties'])
                            if isinstance(item.get('major_issues'), list):
                                item['major_issues'] = ", ".join(item['major_issues'])
                    return constituency_data

                def add_constituency_handler(name, district, parties_str, mla, issues_str):
                    key_parties = [p.strip() for p in parties_str.split(',') if p.strip()]
                    major_issues = [i.strip() for i in issues_str.split(',') if i.strip()]
                    if constituency_db.add_constituency(name, district, key_parties, mla, major_issues):
                        update_constituency_display()
                        return "Constituency added successfully.", "", "", "", "", None
                    else:
                        return "Failed to add constituency (name might already exist or fields missing).", name, district, parties_str, mla, issues_str

                def update_selected_constituency_handler(data, selected_row_index):
                    if selected_row_index is None or not data:
                        return "Please select a constituency row to update.", "", "", "", "", None
                    selected_constituency = data[selected_row_index]
                    name = selected_constituency['name']
                    district = selected_constituency['district']
                    key_parties = [p.strip() for p in selected_constituency['key_parties'].split(',') if p.strip()]
                    mla = selected_constituency['incumbent_mla']
                    major_issues = [i.strip() for i in selected_constituency['major_issues'].split(',') if i.strip()]
                    if constituency_db.update_constituency(name, district, key_parties, mla, major_issues):
                        update_constituency_display()
                        return f"Constituency '{name}' updated.", "", "", "", "", None
                    else:
                        return f"Failed to update constituency '{name}'.", name, district, ", ".join(key_parties), mla, ", ".join(major_issues)

                def remove_selected_constituency_handler(data, selected_row_index):
                    if selected_row_index is None or not data:
                        return "Please select a constituency row to remove.", None
                    selected_constituency = data[selected_row_index]
                    name_to_remove = selected_constituency['name']
                    if constituency_db.remove_constituency(name_to_remove):
                        update_constituency_display()
                        return f"Constituency '{name_to_remove}' removed.", None
                    else:
                        return f"Failed to remove constituency '{name_to_remove}'.", selected_row_index

                def update_constituency_display():
                    constituencies = constituency_db.get_all_constituencies()
                    return pd.DataFrame(constituency_to_str_lists(constituencies))

                def handle_constituency_row_select(evt: gr.SelectData):
                    selected_constituency_data = constituency_db.get_all_constituencies()
                    if evt.index < len(selected_constituency_data):
                        row = selected_constituency_data[evt.index]
                        parties_str = ", ".join(row.get('key_parties', []))
                        issues_str = ", ".join(row.get('major_issues', []))
                        return row['name'], row['district'], parties_str, row['incumbent_mla'], issues_str, evt.index
                    return "", "", "", "", "", None

                add_constituency_btn.click(
                    add_constituency_handler,
                    inputs=[const_name_input, district_input, parties_input, mla_input, issues_input],
                    outputs=[gr.update(value=""), const_name_input, district_input, parties_input, mla_input, issues_input]
                ).then(update_constituency_display, outputs=constituency_data_output)

                constituency_data_output.select(handle_constituency_row_select, inputs=None, outputs=[const_name_input, district_input, parties_input, mla_input, issues_input, gr.State()])

                update_constituency_btn.click(
                    update_selected_constituency_handler,
                    inputs=[constituency_data_output, gr.State()],
                    outputs=[gr.update(value=""), const_name_input, district_input, parties_input, mla_input, issues_input]
                ).then(update_constituency_display, outputs=constituency_data_output)

                remove_constituency_btn.click(
                    remove_selected_constituency_handler,
                    inputs=[constituency_data_output, gr.State()],
                    outputs=[gr.update(value=""), gr.State()]
                ).then(update_constituency_display, outputs=constituency_data_output)

                constituency_data_output.value = update_constituency_display()

        save_btn = gr.Button("Save All Database Changes")
        save_status_msg = gr.Textbox(label="Save Status", interactive=False)
        save_btn.click(update_db_files, outputs=save_status_msg)

    return data_management_tab

def create_scraper_tab():
    with gr.Blocks() as scraper_tab:
        gr.Markdown("# Web Scraper")
        gr.Markdown("Fetch raw HTML content from a given URL.")

        with gr.Row():
            url_input = gr.Textbox(label="Enter URL to scrape", placeholder="e.g., https://example.com")
            scrape_btn = gr.Button("Scrape URL")

        scraped_html_output = gr.Textbox(label="Scraped HTML Content", lines=15, interactive=False)
        scrape_error_output = gr.Textbox(label="Scraping Status/Errors", interactive=False)

        def perform_scrape(url):
            if not url.strip():
                return "", "Please enter a URL."
            content = scraper.scrape_custom_url(url)
            if "Failed to retrieve content" in content:
                return "", content
            else:
                return content, f"Successfully scraped {url}"

        scrape_btn.click(
            perform_scrape,
            inputs=url_input,
            outputs=[scraped_html_output, scrape_error_output]
        )
    return scraper_tab

def create_about_tab():
    with gr.Blocks() as about_tab:
        gr.Markdown("# About TN Election Predictor")
        gr.Markdown(
            """
            This application provides tools for analyzing political data related to Tamil Nadu elections.

            **Features:**
            *   **Text Analysis:** Perform sentiment analysis and predict candidate/party relevance based on text input.
            *   **Web Scraping:** Fetch raw HTML content from specified URLs.
            *   **Data Management:** Manage a local database of candidates and constituencies, which are saved to JSON files.
            *   **Information about Constituencies:** View details for various constituencies in Tamil Nadu.

            **Models Used:**
            *   Sentiment Analysis: `cardiffnlp/twitter-roberta-base-sentiment-latest` (Transformers)
            *   Zero-Shot Classification (Prediction): `facebook/bart-large-mnli` (Transformers)

            **Data Sources:**
            *   Candidate and Constituency data is managed locally and can be updated via the 'Data Management' tab.
            *   News articles are scraped from Google News (with limitations).

            **Note:** This application uses placeholder data and basic scraping. Real-world election prediction requires more sophisticated data sourcing, advanced NLP techniques, and careful handling of data privacy and ethical considerations.
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
    return about_tab

# --- Gradio Interface Setup ---
with gr.Blocks(css="static/styles.css") as demo:
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
    if not os.path.exists("data"):
        os.makedirs("data")
        print("Created 'data' directory.")

    if not os.path.exists("data/candidates.json"):
        print("Initializing candidates.json with default data.")
        candidate_db.load_data()

    if not os.path.exists("data/constituencies.json"):
        print("Initializing constituencies.json with default data.")
        constituency_db.load_data()

    print("Starting Gradio interface...")
    demo.launch()
