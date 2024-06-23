import re
import gradio as gr
import src.translation_agent as ta
from polyglot.detect import Detector
from polyglot.text import Text
from difflib import Differ
from icecream import ic

def lang_detector(text):
    min_chars = 5
    if len(text) < min_chars:
        return "Input text too short"
    try:
        detector = Detector(text).language
        lang_info = str(detector)
        code = re.search(r"name: (\w+)", lang_info).group(1)
        return code
    except Exception as e:
        return f"ERROR：{str(e)}"

def tokenize(text):
    # Use polyglot to tokenize the text
    polyglot_text = Text(text)
    words = polyglot_text.words

    # Check if the text contains spaces
    if ' ' in text:
        # Create a list of words and spaces
        tokens = []
        for word in words:
            tokens.append(word)
            tokens.append(' ')  # Add space after each word
        return tokens[:-1]  # Remove the last space
    else:
        return words

def diff_texts(text1, text2):
    tokens1 = tokenize(text1)
    tokens2 = tokenize(text2)

    d = Differ()
    diff_result = list(d.compare(tokens1, tokens2))

    highlighted_text = []
    for token in diff_result:
        word = token[2:]
        category = None
        if token[0] == '+':
            category = 'added'
        elif token[0] == '-':
            category = 'removed'
        elif token[0] == '?':
            continue  # Ignore the hints line

        highlighted_text.append((word, category))
        ic(highlighted_text)

    return highlighted_text

def huanik(
    endpoint,
    model,
    api_key,
    source_lang,
    target_lang,
    source_text,
    country,
    max_tokens
):

    ic(source_text)
    if not source_text or source_lang == target_lang:
        raise gr.Error("Please check the contents and options right.")

    ta.model_load(endpoint, model, api_key)

    source_text =  re.sub(r'\n+', '\n', source_text)

    init_translation, reflect_translation, final_translation = ta.translate(
        source_lang=source_lang,
        target_lang=target_lang,
        source_text=source_text,
        country=country,
        max_tokens=max_tokens,
    )

    final_diff = gr.HighlightedText(
        diff_texts(init_translation, final_translation),
        label="Diff translation",
        combine_adjacent=True,
        show_legend=True,
        visible=True,
        color_map={"removed": "red", "added": "green"})

    return init_translation, reflect_translation, final_translation, final_diff

TITLE = """
<h1><a href="https://github.com/andrewyng/translation-agent">Translation-Agent</a> webUI</h1>
<center>
Default to using Groq API and llama3-70b models
<br>
Change to OpenAI, Cohere, TogetherAI, Ollama with API and Model
<br>
Source Language auto detected, input your Target language and country.
</center>
"""
CSS = """
    h1 {
        text-align: center;
        display: block;
    }
    footer {
        visibility: hidden;
    }
    .texts {
        min-height: 100px;
    }
"""

with gr.Blocks(theme="soft", css=CSS) as demo:
    gr.Markdown(TITLE)
    with gr.Row():
        with gr.Column(scale=1):
            endpoint = gr.Dropdown(
                label="Endpoint",
                choices=["Groq","OpenAI","Cohere","TogetherAI","Ollama"],
                value="Groq",
            )
            model = gr.Textbox(label="Model", value="llama3-70b-8192", )
            api_key = gr.Textbox(label="API_KEY", type="password", )
            source_lang = gr.Textbox(
                label="Source Lang(Auto-Detect)",
                value="English",
            )
            target_lang = gr.Textbox(
                label="Target Lang",
                value="Spanish",
            )
            country = gr.Textbox(label="Country", value="Argentina", max_lines=1)
            max_tokens = gr.Slider(
                label="Max tokens",
                minimum=512,
                maximum=2046,
                value=1000,
                step=8,
                )
        with gr.Column(scale=4):
            source_text = gr.Textbox(
                label="Source Text",
                value="How we live is so different from how we ought to live that he who studies "+\
                "what ought to be done rather than what is done will learn the way to his downfall "+\
                "rather than to his preservation.",
                elem_classes="texts",
            )
            with gr.Tab("Final"):
                output_final = gr.Textbox(label="FInal Translation", elem_classes="texts")
            with gr.Tab("Initial"):
                output_init = gr.Textbox(label="Init Translation", elem_classes="texts")
            with gr.Tab("Reflection"):
                output_reflect = gr.Markdown(label="Reflection")
            with gr.Tab("Diff"):
                output_diff = gr.HighlightedText(visible = False)
    with gr.Row():
        submit = gr.Button(value="Submit")
        clear = gr.ClearButton([source_text, output_init, output_reflect, output_final])

    source_text.change(lang_detector, source_text, source_lang)
    submit.click(fn=huanik, inputs=[endpoint, model, api_key, source_lang, target_lang, source_text, country, max_tokens], outputs=[output_init, output_reflect, output_final, output_diff])

if __name__ == "__main__":
    demo.queue(api_open=False).launch(show_api=False, share=False)
