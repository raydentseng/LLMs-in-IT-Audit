import fitz
import os
from PIL import Image
import base64
from openai import OpenAI
import random

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
)

PROMPTING_METHODS = ["Zero-shot", "One-shot", "Chain-of-Thought"]
persona = "You are an experienced IT auditor with expertise in evaluating access controls within financial audits. You apply professional judgment and maintain professional skepticism when evaluating whether the provided evidence supports the control description."
task = "Your task is to carefully analyze the provided evidence to determine whether it sufficiently supports the described control."
reasoning = """
Before answering, carefully consider the following steps:
    - What actions and approvals are required according to the control description?
    - Which actions are demonstrated in the evidence, and who performed them?
    - Does the sequence and completeness of the evidence sufficiently support the control's effectiveness?
"""
question = "Based on the evidence, answer the questions according to the following format: \n" 
output_format = """
Identification: Based on the control description, what are the control attributes?

Indication: How do you identify the attributes in the evidence? Specify which actions are taken and where in the evidence you found these.

Completeness: Is any critical evidence missing that would be necessary to confirm the execution or effectiveness of the control?

Remarks: Identify and describe elements in the control description or the evidence that are ambiguous, inconsistent, or require further clarification. Explain why these stand out and what additional information would help to resolve these issues.

Conclusion: Based on your analysis, classify the case into one of the following categories:

A. Fully supports - evidence is complete and confirms the correct execution of the control.
B. Does not fully support - evidence is incomplete or unclear and may require additional clarification, no clear deficiency is indicated.
C. Does not support - evidence violates the control description.

Justify your classification with a brief explanation.
"""

# Function to encode the image
def encode_image_gpt(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def list_files_in_directory(directory):
    if not os.path.exists(directory):
        print(f"[!] Directory '{directory}' does not exist.")
        return []
    return [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]


def prepare_output_dir(base_output_dir, file_identifier):
    output_dir = os.path.join(base_output_dir, file_identifier)
    os.makedirs(output_dir, exist_ok=True)
    return output_dir

def convert_pdf_pages_to_images(pdf_path, output_dir, unique_prefix):
    image_filenames = []

    try:
        pdf_file = fitz.open(pdf_path)
    except Exception as e:
        print(f"[!] Failed to open {pdf_path}: {e}")
        return image_filenames

    for page_index in range(len(pdf_file)):
        page = pdf_file.load_page(page_index)
        pix = page.get_pixmap()  # Render pagina naar bitmap
        image_name = f"{unique_prefix}_page_{page_index + 1}.png"
        image_path = os.path.join(output_dir, image_name)
        zoom = 2.0  # 2x vergroting

        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat)
        pix.save(image_path)
        image_filenames.append(image_path)

    return image_filenames

def load_control_description(subdir_path, file_counter):
    txt_filename = f"ctrl_{file_counter}.txt"  # Bijvoorbeeld ctrl_1.txt
    txt_path = os.path.join(subdir_path, txt_filename)
    
    if not os.path.exists(txt_path):
        print(f"[!] Control description file not found for file {file_counter}: {txt_filename}")
        return ""
    
    with open(txt_path, "r", encoding="utf-8") as f:
        control_description = f.read().strip()
    
    return control_description

def extract_base_case_index(file_id):
    # Extracts the case number from e.g. "file_1" -> returns 1
    return int(file_id.split("_")[1])

def select_example_case(current_case_idx, total_cases=8):
    # Determine excluded indices: base and variant (e.g. 1 and 5)
    excluded = {current_case_idx, current_case_idx + 4} if current_case_idx <= 4 else {current_case_idx, current_case_idx - 4}
    eligible = [i for i in range(1, total_cases + 1) if i not in excluded]
    return random.choice(eligible)

def load_example_prompt(example_idx, base_dir="./Human Evaluation"):
    tod_folder = f"TOD {example_idx}"
    folder_path = os.path.join(base_dir, tod_folder)

    # Load control description
    ctrl_path = os.path.join(folder_path, f"ctrl_{example_idx}.txt")
    if not os.path.exists(ctrl_path):
        print(f"[!] Missing control description for TOD {example_idx}")
        return None, [], None

    with open(ctrl_path, "r", encoding="utf-8") as f:
        control_text = f.read().strip()

    # Load human evaluation
    eval_path = os.path.join(folder_path, f"eval_{example_idx}.txt")
    if not os.path.exists(eval_path):
        print(f"[!] Missing evaluation file for TOD {example_idx}")
        return None, [], None

    with open(eval_path, "r", encoding="utf-8") as f:
        evaluation_text = f.read().strip()

    # Load associated images
    image_files = sorted([
        os.path.join(folder_path, f) for f in os.listdir(folder_path)
        if f.lower().endswith(".png")
    ])

    return control_text, image_files, evaluation_text


def build_prompts_for_file(file_id, image_paths, prompting_methods, control_description):
    prompts = {}
    case_idx = extract_base_case_index(file_id)

    for method in prompting_methods:
        prompt_text = f"{persona}\n{task}"
        full_images = image_paths[:]

        if method.lower() == "zero-shot":
            prompt_text += f"\nConsider the following control description:\n\n{control_description}\n\n{question}{output_format}"
            pass  # Use base prompt

        elif method.lower() == "chain-of-thought":
            prompt_text += f"\nConsider the following control description:\n\n{control_description}\n\n{question}{output_format}"
            prompt_text += "Let's think this step-by-step."

        elif method.lower() == "one-shot":
            # Add one-shot example
            example_idx = select_example_case(case_idx)
            example_text, example_images, evaluation_text = load_example_prompt(example_idx)

            if example_text:
                prompt_text += f"\nThese is an example case attached with filenames {example_images}. You do not have to assess this case. It serves as a reference and has the control description:\n\n{example_text}"
                prompt_text += f"\n\nWith example evaluation:\n\n{evaluation_text}"
                full_images += example_images
                prompt_text += f"\n\n\nNow consider the other case with filenames {image_paths} with the following control description:\n\n{control_description}\n\n{question}{output_format}"
            else:
                print(f"[!] Skipping example for {file_id} due to missing data.")

        prompts[method] = {
            "text": prompt_text,
            "images": full_images,
        }

    return prompts


def write_prompt_outputs(all_prompts, output_dir):
    base_output_path = os.path.join(output_dir, "generated_output")
    os.makedirs(base_output_path, exist_ok=True)

    for file_id, methods in all_prompts.items():
        case_output_dir = os.path.join(base_output_path, file_id)
        os.makedirs(case_output_dir, exist_ok=True)

        for method, prompt in methods.items():
            method_dir = os.path.join(case_output_dir, method.replace(" ", "_"))
            os.makedirs(method_dir, exist_ok=True)

            input_file_path = os.path.join(method_dir, "input.txt")
            output_file_path = os.path.join(method_dir, "output.txt")

            with open(input_file_path, "w", encoding="utf-8") as f_in:
                f_in.write(prompt["text"])

            with open(output_file_path, "w", encoding="utf-8") as f_out:
                f_out.write(prompt.get("response", ""))  # empty if not yet generated


def process_all_files(input_dir, output_dir, prompting_methods):
    all_prompts = {}
    file_counter = 1

    # Eerst alle submappen ophalen en sorteren op nummer
    subdirs = [d for d in os.listdir(input_dir) if os.path.isdir(os.path.join(input_dir, d))]
    subdirs = sorted(subdirs, key=lambda x: int(x.split('TOD ')[-1]))

    # Dan iteratief over elke submap gaan
    for subdir_name in subdirs:
        subdir_path = os.path.join(input_dir, subdir_name)

        for file in os.listdir(subdir_path):
            if not file.lower().endswith('.pdf'):
                continue

            file_id = f"file_{file_counter}"
            input_path = os.path.join(subdir_path, file)
            output_subdir = prepare_output_dir(output_dir, file_id)

            image_path = convert_pdf_pages_to_images(input_path, output_subdir, file_id)
            control_description = load_control_description(subdir_path, file_counter)
            prompts = build_prompts_for_file(file_id, image_path, prompting_methods, control_description)

            all_prompts[file_id] = prompts
            file_counter += 1

    return all_prompts



def gpt4o_mini(image_paths, description_text):
    content = [{"type": "input_text", "text": description_text}]

    for path in image_paths:
        try:
            base64_image = encode_image_gpt(path)
            # Add image to the content list
            content.append({
                "type": "input_image",
                "image_url": f"data:image/jpeg;base64,{base64_image}",
            })
        except Exception as e:
            print(f"Failed to encode {path}: {e}")

    # Send the request
    response = client.responses.create(
        model="gpt-4o-mini",
        input=[
            {
                "role": "user",
                "content": content,
            }
        ],
    )
    print(response.output_text)
    return response.output_text

def gpto4_mini(image_paths, description_text):
    content = [{"type": "input_text", "text": description_text}]

    for path in image_paths:
        try:
            base64_image = encode_image_gpt(path)
            # Add image to the content list
            content.append({
                "type": "input_image",
                "image_url": f"data:image/jpeg;base64,{base64_image}",
            })
        except Exception as e:
            print(f"Failed to encode {path}: {e}")

    # Send the request
    response = client.responses.create(
        model="o4-mini",
        reasoning={"effort": "high"},
        input=[
            {
                "role": "user",
                "content": content,
            }
        ],
    )
    print(response.output_text)
    return response.output_text

def run_all_api_calls(all_prompts):
    for file_id, methods in all_prompts.items():
        print(f"\n🔍 Running APIs for {file_id}")
        for method, prompt in methods.items():
            print(f"  → {method.upper()}")

            image_paths = prompt["images"]
            description = prompt["text"]

            # Call all APIs

            response1 = gpto4_mini(image_paths, description)
            response2 = gpt4o_mini(image_paths, description)


            prompt["response"] = response1

            # Immediately write the result to output.txt
            case_output_dir_1 = os.path.join("./generated_output_gpt_o4_mini", file_id, method.replace(" ", "_"))
            case_output_dir_2 = os.path.join("./generated_output_gpt_4o_mini", file_id, method.replace(" ", "_"))
            os.makedirs(case_output_dir_1, exist_ok=True)
            os.makedirs(case_output_dir_2, exist_ok=True)

            input_file_path_1 = os.path.join(case_output_dir_1, "input.txt")
            output_file_path_1 = os.path.join(case_output_dir_1, "output.txt")

            input_file_path_2 = os.path.join(case_output_dir_2, "input.txt")
            output_file_path_2 = os.path.join(case_output_dir_2, "output.txt")

            with open(input_file_path_1, "w", encoding="utf-8") as f_in:
                f_in.write(description)

            with open(output_file_path_1, "w", encoding="utf-8") as f_out:
                f_out.write(response1 if isinstance(response1, str) else str(response1))

            with open(input_file_path_2, "w", encoding="utf-8") as f_in:
                f_in.write(description)

            with open(output_file_path_2, "w", encoding="utf-8") as f_out:
                f_out.write(response2 if isinstance(response2, str) else str(response1))


def main():
    input_dir = "./Evidence"
    output_dir = "./Output"
    generated_dir = "./"
    all_prompts = process_all_files(input_dir, output_dir, PROMPTING_METHODS)

    run_all_api_calls(all_prompts)

if __name__ == "__main__":
    main()
