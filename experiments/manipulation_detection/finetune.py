import os
import warnings
warnings.filterwarnings('ignore')

import argparse
from sklearn.metrics import precision_score, recall_score, f1_score, accuracy_score, confusion_matrix
from sklearn.model_selection import train_test_split

from utils import *
from load_data import LoadManipDataset, LoadOtherDataset
from model_llama import LlamaModel
from model_roberta import RoBERTaModel


def prediction(model, test_data):
    answer_column = 'Manipulative'
    if 'Manipulative' not in test_data.columns:
        answer_column = 'Toxicity'
    targets = [int(v) for v in test_data[answer_column].values]
    preds = []
    count = 0
    for idx, row in test_data.iterrows():
        count += 1
        logging.info(f"-----Running {model.model_id} zeroshot prompting ({count}/{len(test_data)})-----")
        dialogue = row['Dialogue']
        pred = model.zeroshot_prompting(dialogue)
        preds.append(pred)

    corrupted_result = 0
    processed_preds, processed_targets = [], []
    for pred, target in zip(preds, targets):
        if pred == -1:
            corrupted_result += 1
        else:
            processed_preds.append(pred)
            processed_targets.append(target)

    logging.info(f"\n----------{model.model_id} finetuning result----------")
    logging.info(
        f"Out of {len(preds)} test samples, corrupted samples: {corrupted_result}, processed samples: {len(processed_preds)}")

    # Calculate metrics
    precision = precision_score(processed_targets, processed_preds, zero_division=0)
    recall = recall_score(processed_targets, processed_preds, zero_division=0)
    micro_f1 = f1_score(processed_targets, processed_preds, average='micro', zero_division=0)
    macro_f1 = f1_score(processed_targets, processed_preds, average='macro', zero_division=0)
    accuracy = accuracy_score(processed_targets, processed_preds)
    conf_matrix = confusion_matrix(processed_targets, processed_preds)

    # Print results
    logging.info(
        f"Golden manipulative samples = {len([v for v in processed_targets if v == 1])}, non-manipulative samples = {len([v for v in processed_targets if v == 0])}")
    logging.info(
        f"Predicted manipulative samples = {len([v for v in processed_preds if v == 1])}, non-manipulative samples = {len([v for v in processed_preds if v == 0])}")
    logging.info(f"- Precision = {precision:.3f}")
    logging.info(f"- Recall = {recall:.3f}")
    logging.info(f"- Accuracy = {accuracy:.3f}")
    logging.info(f"- Micro F1-Score = {micro_f1:.3f}")
    logging.info(f"- Macro F1-Score = {macro_f1:.3f}")
    logging.info(f"- Confusion Matrix = \n{conf_matrix}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='finetune')
    parser.add_argument('--model', default='llama-13b', type=str)
    parser.add_argument('--temp', default=0.1, type=float)
    parser.add_argument('--top_p', default=0.5, type=float)
    parser.add_argument('--penal', default=0.0, type=float)
    parser.add_argument('--log_dir', default='./logs', type=str)
    parser.add_argument('--epoch', default=3, type=int)
    parser.add_argument('--train_batch_size', default=8, type=int)
    parser.add_argument('--valid_batch_size', default=8, type=int)
    parser.add_argument('--lr', default=0.0001, type=float)
    parser.add_argument('--train_data', default='Dreaddit', type=str)
    args = parser.parse_args()

    if os.path.exists(args.log_dir) is False:
        os.makedirs(args.log_dir)

    set_logging(args, parser.description)
    show_args(args)

    manip_dataset = LoadManipDataset(file_name='../dataset/new_processed_mentalmanip_con_final.csv',
                                     train_ratio=0.6,
                                     valid_ratio=0.2,
                                     test_ratio=0.2)

    if args.train_data != 'mentalmanip':
        train_dataset = LoadOtherDataset(file_name='../dataset/'+args.train_data+'/dataset.csv')
        if len(train_dataset.df) >= 5000:
            cutted_size = 5000
            logging.info(f"-----Downsampling Dataset {args.train_data} to size {cutted_size}-----")
            train_dataset.df = train_dataset.df.sample(n=cutted_size, random_state=42).reset_index(drop=True)
        train_data, valid_data = train_test_split(train_dataset.df, test_size=0.2, random_state=42)
    else:
        train_data = manip_dataset.df_train
        valid_data = manip_dataset.df_valid
        # train_data = train_data.iloc[:500]
    test_data = manip_dataset.df_test

    logging.info(f"-----Finetuning Data Size Information-----")
    logging.info(f"Train size: {len(train_data)}")
    logging.info(f"Valid size: {len(valid_data)}")
    logging.info(f"Test size: {len(test_data)}")
    logging.info("")

    if 'llama' in args.model:
        llama_model = "Llama-2-7b-chat-hf"
        if '13b' in args.model:
            llama_model = "Llama-2-13b-chat-hf"

        # modelLlama = LlamaModel(load_from_local=False,
        #                         model=llama_model,
        #                         temperature=0.6,
        #                         top_p=0.9,
        #                         top_k=50,
        #                         repetition_penalty=1.2,
        #                         max_new_tokens=1024,
        #                         max_input_token_length=4096,
        #                         ft_output_dir='llama_ft_maj/'+args.train_data)
        # modelLlama.finetuning(train_data,
        #                       valid_data,
        #                       test_data,
        #                       epochs=args.epoch,
        #                       train_batch_size=args.train_batch_size,
        #                       lr=args.lr)

        modelLlama = LlamaModel(load_from_local=True,
                                model='llama_ft_maj/'+args.train_data,
                                temperature=0.6,
                                top_p=0.9,
                                top_k=50,
                                repetition_penalty=1.2,
                                max_new_tokens=1024,
                                max_input_token_length=4096,
                                ft_output_dir='llama_ft_maj/'+args.train_data)
        prediction(modelLlama, test_data)

    elif 'roberta' in args.model:
        roberta_model = "roberta-base"
        if 'large' in args.model:
            roberta_model = "roberta-large"

        modelRoBERTa = RoBERTaModel(model=roberta_model,
                                    max_length=512,
                                    train_batch_size=args.train_batch_size,
                                    valid_batch_size=args.valid_batch_size,
                                    epochs=args.epoch,
                                    learning_rate=args.lr,
                                    output_dir='roberta_ft/'+args.train_data)
        modelRoBERTa.finetuning(train_data, valid_data, test_data)
