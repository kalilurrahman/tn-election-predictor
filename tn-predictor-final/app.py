import gradio as gr
from src.scraper import ElectionScraper
from src.sentiment import SentimentAnalyzer
from src.predictor import ElectionPredictor
from src.candidate_db import CandidateDB
from src.constituency import ConstituencyData
import pandas as pd
import os
import sys

# --- Path Correction ---
try:
    import src.utils
except ImportError:
    current_dir = os.path.dirname(__file__)
    if os.path.exists(os.path.join(current_dir, 'src')):
        sys.path.insert(0, current_dir)

# --- Ensure data directory exists early ---
os.makedirs("data", exist_ok=True)

# --- Initialize core modules ---
candidate_db = CandidateDB(file_path="data/candidates.json")
constituency_db = ConstituencyData(file_path="data/constituencies.json")
scraper = ElectionScraper()
sentiment_analyzer = SentimentAnalyzer()
predictor = ElectionPredictor()


def update_db_files():
    candidate_db.save_data()
    constituency_db.save_data()
    return "Database files saved successfully."


# ──────────────────────────────────────────────
# TAB 1: Prediction & Analysis
# ──────────────────────────────────────────────
def create_prediction_tab():
    with gr.Blocks() as prediction_tab:
        gr.Markdown("# Election Prediction based on Text Analysis")
        gr.Markdown(
            "Analyze news articles, social media posts, or any text to gauge "
            "sentiment and predict relevance to candidates/parties."
        )

        with gr.Row():
            text_input = gr.Textbox(
                label="Enter Text for Analysis",
                lines=5,
                placeholder="Paste news headlines, political commentary, social media posts here...",
            )
            candidates_list_str = gr.Textbox(
                label="Candidates/Parties (comma-separated)",
                value=",".join(candidate_db.get_all_candidate_names()),
                placeholder="e.g., M. K. Stalin, AIADMK, BJP",
            )

        with gr.Row():
            num_preds_slider = gr.Slider(
                minimum=1, maximum=10, step=1, value=5, label="Number of Top Predictions"
            )
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
                [
                    "The ruling DMK party held a massive rally in Madurai. CM M. K. Stalin "
                    "spoke about government achievements and criticized AIADMK. BJP leader "
                    "K. Annamalai was in Coimbatore meeting with party workers.",
                    "M. K. Stalin, DMK, AIADMK, BJP, Kamal Haasan, MNM",
                ],
                [
                    "New economic policy faces criticism. Focus on industrial growth seen as "
                    "neglecting agriculture, a major concern in Tamil Nadu.",
                    "DMK, AIADMK, BJP, Congress",
                ],
            ],
            inputs=[text_input, candidates_list_str],
        )

        def perform_analysis(text, candidates_str, num_preds):
            if not text.strip():
                return {"label": "Neutral", "score": 0.0, "warning": "No text provided."}, [], []
            candidate_list = [c.strip() for c in candidates_str.split(",") if c.strip()]
            if not candidate_list:
                return {"label": "Neutral", "score": 0.0, "warning": "No candidates provided."}, [], []

            sentiment = sentiment_analyzer.analyze(text)
            predictions = predictor.predict(text, candidate_list, num_predictions=int(num_preds))
            scraped_news = []
            if len(text.split()) > 5 and any(
                w in text.lower() for w in ["election", "politics", "candidate", "party", "rally", "vote"]
            ):
                query_text = text[:100]
                scraped_news = scraper.scrape_news_articles(
                    query=f"Tamil Nadu {query_text}", num_articles=3
                )
                if not scraped_news:
                    scraped_news = [{"title": "No relevant news found.", "url": "#", "source": "N/A"}]

            return sentiment, predictions, scraped_news

        analyze_btn.click(
            perform_analysis,
            inputs=[text_input, candidates_list_str, num_preds_slider],
            outputs=[sentiment_output, prediction_output, scraped_news_output],
        )
    return prediction_tab


# ──────────────────────────────────────────────
# TAB 2: Data Management
# ──────────────────────────────────────────────
def create_data_management_tab():
    with gr.Blocks() as data_management_tab:
        gr.Markdown("# Data Management")
        gr.Markdown(
            "Manage candidate and constituency data. Changes are saved to local JSON files."
        )

        with gr.Tabs():
            # ── Candidate Management ──
            with gr.TabItem("Candidate Management"):
                gr.Markdown("## Candidates")
                with gr.Row():
                    with gr.Column():
                        name_input = gr.Textbox(label="Candidate Name")
                        party_input = gr.Textbox(label="Party")
                        constituency_input = gr.Textbox(label="Constituency")
                        status_input = gr.Textbox(label="Status", value="Active")
                        activity_input = gr.Textbox(label="Recent Activity", lines=2)
                        cand_msg = gr.Textbox(label="Status Message", interactive=False)
                        with gr.Row():
                            add_candidate_btn = gr.Button("Add Candidate")
                            update_candidate_btn = gr.Button("Update Selected")
                            remove_candidate_btn = gr.Button("Remove Selected")
                    with gr.Column():
                        candidate_data_output = gr.DataFrame(
                            headers=["name", "party", "constituency", "status", "recent_activity"],
                            interactive=True,
                            label="Current Candidates",
                        )

                selected_candidate_index = gr.State(value=None)

                def get_candidate_df():
                    candidates = candidate_db.get_all_candidates()
                    if candidates:
                        return pd.DataFrame(candidates)
                    return pd.DataFrame(
                        columns=["name", "party", "constituency", "status", "recent_activity"]
                    )

                def add_candidate_handler(name, party, constituency, status, activity):
                    if candidate_db.add_candidate(name, party, constituency, status, activity):
                        return "Candidate added successfully.", "", "", "", "Active", ""
                    return "Failed to add candidate (name may already exist).", name, party, constituency, status, activity

                def update_candidate_handler(data, idx, name, party, constituency, status, activity):
                    if idx is None:
                        return "Select a row first.", name, party, constituency, status, activity
                    if candidate_db.update_candidate_status_and_activity(name, status, activity):
                        return f"'{name}' updated.", name, party, constituency, status, activity
                    return f"Failed to update '{name}'.", name, party, constituency, status, activity

                def remove_candidate_handler(data, idx):
                    if idx is None:
                        return "Select a row first.", None
                    rows = candidate_db.get_all_candidates()
                    if idx < len(rows):
                        name = rows[idx]["name"]
                        if candidate_db.remove_candidate(name):
                            return f"'{name}' removed.", None
                    return "Failed to remove candidate.", idx

                def handle_candidate_select(evt: gr.SelectData):
                    rows = candidate_db.get_all_candidates()
                    if evt.index < len(rows):
                        r = rows[evt.index]
                        return (
                            r["name"], r["party"], r["constituency"],
                            r["status"], r.get("recent_activity", ""), evt.index
                        )
                    return "", "", "", "Active", "", None

                add_candidate_btn.click(
                    add_candidate_handler,
                    inputs=[name_input, party_input, constituency_input, status_input, activity_input],
                    outputs=[cand_msg, name_input, party_input, constituency_input, status_input, activity_input],
                ).then(get_candidate_df, outputs=candidate_data_output)

                candidate_data_output.select(
                    handle_candidate_select,
                    outputs=[name_input, party_input, constituency_input, status_input, activity_input, selected_candidate_index],
                )

                update_candidate_btn.click(
                    update_candidate_handler,
                    inputs=[candidate_data_output, selected_candidate_index, name_input, party_input, constituency_input, status_input, activity_input],
                    outputs=[cand_msg, name_input, party_input, constituency_input, status_input, activity_input],
                ).then(get_candidate_df, outputs=candidate_data_output)

                remove_candidate_btn.click(
                    remove_candidate_handler,
                    inputs=[candidate_data_output, selected_candidate_index],
                    outputs=[cand_msg, selected_candidate_index],
                ).then(get_candidate_df, outputs=candidate_data_output)

            # ── Constituency Management ──
            with gr.TabItem("Constituency Management"):
                gr.Markdown("## Constituencies")
                with gr.Row():
                    with gr.Column():
                        const_name_input = gr.Textbox(label="Constituency Name")
                        district_input = gr.Textbox(label="District")
                        parties_input = gr.Textbox(
                            label="Key Parties (comma-separated)",
                            placeholder="e.g., DMK,AIADMK,BJP",
                        )
                        mla_input = gr.Textbox(label="Incumbent MLA")
                        issues_input = gr.Textbox(
                            label="Major Issues (comma-separated)",
                            placeholder="e.g., Water,Roads",
                        )
                        const_msg = gr.Textbox(label="Status Message", interactive=False)
                        with gr.Row():
                            add_constituency_btn = gr.Button("Add Constituency")
                            update_constituency_btn = gr.Button("Update Selected")
                            remove_constituency_btn = gr.Button("Remove Selected")
                    with gr.Column():
                        constituency_data_output = gr.DataFrame(
                            headers=["name", "district", "key_parties", "incumbent_mla", "major_issues"],
                            interactive=True,
                            label="Current Constituencies",
                        )

                selected_constituency_index = gr.State(value=None)

                def stringify_lists(items):
                    for item in items:
                        if isinstance(item.get("key_parties"), list):
                            item["key_parties"] = ", ".join(item["key_parties"])
                        if isinstance(item.get("major_issues"), list):
                            item["major_issues"] = ", ".join(item["major_issues"])
                    return items

                def get_constituency_df():
                    constituencies = constituency_db.get_all_constituencies()
                    if constituencies:
                        return pd.DataFrame(stringify_lists(constituencies))
                    return pd.DataFrame(
                        columns=["name", "district", "key_parties", "incumbent_mla", "major_issues"]
                    )

                def add_constituency_handler(name, district, parties_str, mla, issues_str):
                    key_parties = [p.strip() for p in parties_str.split(",") if p.strip()]
                    major_issues = [i.strip() for i in issues_str.split(",") if i.strip()]
                    if constituency_db.add_constituency(name, district, key_parties, mla, major_issues):
                        return "Constituency added.", "", "", "", "", ""
                    return "Failed to add (name may exist).", name, district, parties_str, mla, issues_str

                def update_constituency_handler(data, idx, name, district, parties_str, mla, issues_str):
                    if idx is None:
                        return "Select a row first.", name, district, parties_str, mla, issues_str
                    key_parties = [p.strip() for p in parties_str.split(",") if p.strip()]
                    major_issues = [i.strip() for i in issues_str.split(",") if i.strip()]
                    if constituency_db.update_constituency(name, district, key_parties, mla, major_issues):
                        return f"'{name}' updated.", name, district, parties_str, mla, issues_str
                    return f"Failed to update '{name}'.", name, district, parties_str, mla, issues_str

                def remove_constituency_handler(data, idx):
                    if idx is None:
                        return "Select a row first.", None
                    rows = constituency_db.get_all_constituencies()
                    if idx < len(rows):
                        name = rows[idx]["name"]
                        if constituency_db.remove_constituency(name):
                            return f"'{name}' removed.", None
                    return "Failed to remove.", idx

                def handle_constituency_select(evt: gr.SelectData):
                    rows = constituency_db.get_all_constituencies()
                    if evt.index < len(rows):
                        r = rows[evt.index]
                        parties_str = ", ".join(r.get("key_parties", []))
                        issues_str = ", ".join(r.get("major_issues", []))
                        return (
                            r["name"], r["district"], parties_str,
                            r.get("incumbent_mla", ""), issues_str, evt.index
                        )
                    return "", "", "", "", "", None

                add_constituency_btn.click(
                    add_constituency_handler,
                    inputs=[const_name_input, district_input, parties_input, mla_input, issues_input],
                    outputs=[const_msg, const_name_input, district_input, parties_input, mla_input, issues_input],
                ).then(get_constituency_df, outputs=constituency_data_output)

                constituency_data_output.select(
                    handle_constituency_select,
                    outputs=[const_name_input, district_input, parties_input, mla_input, issues_input, selected_constituency_index],
                )

                update_constituency_btn.click(
                    update_constituency_handler,
                    inputs=[constituency_data_output, selected_constituency_index, const_name_input, district_input, parties_input, mla_input, issues_input],
                    outputs=[const_msg, const_name_input, district_input, parties_input, mla_input, issues_input],
                ).then(get_constituency_df, outputs=constituency_data_output)

                remove_constituency_btn.click(
                    remove_constituency_handler,
                    inputs=[constituency_data_output, selected_constituency_index],
                    outputs=[const_msg, selected_constituency_index],
                ).then(get_constituency_df, outputs=constituency_data_output)

        save_btn = gr.Button("💾 Save All Database Changes")
        save_msg = gr.Textbox(label="Save Status", interactive=False)
        save_btn.click(update_db_files, outputs=save_msg)

    return data_management_tab


# ──────────────────────────────────────────────
# TAB 3: Web Scraper
# ──────────────────────────────────────────────
def create_scraper_tab():
    with gr.Blocks() as scraper_tab:
        gr.Markdown("# Web Scraper")
        gr.Markdown("Fetch raw HTML content from a given URL.")

        with gr.Row():
            url_input = gr.Textbox(
                label="Enter URL to scrape", placeholder="e.g., https://example.com"
            )
            scrape_btn = gr.Button("Scrape URL")

        scraped_html_output = gr.Textbox(
            label="Scraped HTML Content", lines=15, interactive=False
        )
        scrape_error_output = gr.Textbox(label="Status/Errors", interactive=False)

        def perform_scrape(url):
            if not url.strip():
                return "", "Please enter a URL."
            content = scraper.scrape_custom_url(url)
            if "Failed to retrieve content" in content:
                return "", content
            return content, f"Successfully scraped {url}"

        scrape_btn.click(
            perform_scrape,
            inputs=url_input,
            outputs=[scraped_html_output, scrape_error_output],
        )
    return scraper_tab


# ──────────────────────────────────────────────
# TAB 4: About
# ──────────────────────────────────────────────
def create_about_tab():
    with gr.Blocks() as about_tab:
        gr.Markdown("# About TN Election Predictor")
        gr.Markdown(
            """
This application provides tools for analyzing political data related to Tamil Nadu elections.

**Features:**
- **Text Analysis:** Sentiment analysis and candidate/party relevance prediction.
- **Web Scraping:** Fetch raw HTML from any URL.
- **Data Management:** Manage a local database of candidates and constituencies.

**Models Used:**
- Sentiment: `cardiffnlp/twitter-roberta-base-sentiment-latest`
- Zero-Shot Classification: `facebook/bart-large-mnli`

**Note:** Models are downloaded on first run. This may take a few minutes on the initial load.
            """
        )
    return about_tab


# ──────────────────────────────────────────────
# Main Gradio App
# ──────────────────────────────────────────────
css_path = "static/styles.css"
css_content = ""
if os.path.exists(css_path):
    with open(css_path, "r") as f:
        css_content = f.read()

with gr.Blocks(css=css_content, title="TN Election Predictor 2026") as demo:
    gr.Markdown("# 🗳️ Tamil Nadu Election Predictor 2026")

    with gr.Tabs():
        with gr.TabItem("📊 Prediction & Analysis"):
            demo.add(create_prediction_tab())
        with gr.TabItem("🗂️ Data Management"):
            demo.add(create_data_management_tab())
        with gr.TabItem("🌐 Web Scraper"):
            demo.add(create_scraper_tab())
        with gr.TabItem("ℹ️ About"):
            demo.add(create_about_tab())

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860, share=False, show_api=False)
