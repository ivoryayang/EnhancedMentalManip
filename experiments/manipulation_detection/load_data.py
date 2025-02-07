import pandas as pd
import csv
from collections import defaultdict
import seaborn as sns
import matplotlib.pyplot as plt
import logging


class LoadManipDataset:
    def __init__(self, file_name, train_ratio, valid_ratio, test_ratio, split_draw=False):
        self.df = self.import_data(file_name)
        self.train_ratio = train_ratio
        self.valid_ratio = valid_ratio
        self.test_ratio = test_ratio
        self.df_train, self.df_valid, self.df_test = self.split_train_test(split_draw)
        self.techs = None
        self.vuls = None

    def import_data(sel, file_name):
        with open(file_name, 'r', newline='', encoding='utf-8') as infile:
            content = csv.reader(infile, delimiter=',', quoting=csv.QUOTE_MINIMAL)
            data = []
            columns = None
            for idx, row in enumerate(content):
                if idx == 0:
                    columns = row
                else:
                    data.append(row)
        dataframe = pd.DataFrame(data, columns=columns)
        # drop certain columns
        if 'ID' in dataframe.columns:
            dataframe = dataframe.drop(['ID'], axis=1)
        return dataframe

    def split_train_test(self, draw):
        def get_dict(dataframe):
            tech_dict = defaultdict(list)
            vul_dict = defaultdict(list)
            nonmanip_dict = defaultdict(list)
            for idx, row in dataframe.iterrows():
                techs = row['Technique'].split(',')
                vuls = row['Vulnerability'].split(',')
                if techs == [''] or vuls == ['']:
                    nonmanip_dict['nonmanip'].append(idx)
                    continue
                for tech in techs:
                    tech_dict[tech].append(idx)
                for vul in vuls:
                    vul_dict[vul].append(idx)
            return nonmanip_dict, tech_dict, vul_dict

        df_shuffled = self.df.sample(frac=1, random_state=17).reset_index(drop=True)
        # Calculate split sizes
        train_size = int(self.train_ratio * len(df_shuffled))
        valid_size = int(self.valid_ratio * len(df_shuffled))
        test_size = len(df_shuffled) - train_size - valid_size

        # Split the DataFrame randomly
        train = df_shuffled.iloc[:train_size]
        valid = df_shuffled.iloc[train_size:train_size + valid_size]
        test = df_shuffled.iloc[train_size + valid_size:]

        logging.info(f"-----MentalManip Dataset Information-----")
        logging.info(f"Total size = {len(df_shuffled)}, manipulative:non-manipulative ratio = {len(df_shuffled[df_shuffled['Manipulative'] == '1'])/len(df_shuffled[df_shuffled['Manipulative'] == '0']):.3f}")
        logging.info(f"Train size = {len(train)}, manipulative:non-manipulative ratio = {len(train[train['Manipulative'] == '1'])/len(train[train['Manipulative'] == '0']):.3f}")
        logging.info(f"Valid size = {len(valid)}, manipulative:non-manipulative ratio = {len(valid[valid['Manipulative'] == '1'])/len(valid[valid['Manipulative'] == '0']):.3f}")
        logging.info(f"Test size = {len(test)}, manipulative:non-manipulative ratio = {len(test[test['Manipulative'] == '1'])/len(test[test['Manipulative'] == '0']):.3f}")
        logging.info("")

        if draw:
            draw_df = pd.DataFrame(columns=['tech_vul', 'set'])
            for set, data in zip(['train', 'valid', 'test'], [train, valid, test]):
                nonmanip_dict, tech_dict, vul_dict = get_dict(data)
                if set == 'train':
                    self.techs = sorted(list(tech_dict.keys()))
                    self.vuls = sorted(list(vul_dict.keys()))
                for tech, idxes in tech_dict.items():
                    for idx in idxes:
                        draw_df.loc[len(draw_df)] = [tech, set]
                for vul, idxes in vul_dict.items():
                    for idx in idxes:
                        draw_df.loc[len(draw_df)] = [vul, set]

            draw_df['set'] = pd.Categorical(draw_df['set'], categories=['train', 'valid', 'test'], ordered=True)
            draw_df['tech_vul'] = pd.Categorical(draw_df['tech_vul'],
                                                 categories=self.techs+self.vuls, ordered=True)

            # Calculate counts
            grouped = draw_df.groupby(['tech_vul', 'set']).size().reset_index(name='counts')

            # Calculate total counts for each 'tech_vul'
            total_counts = grouped.groupby('tech_vul')['counts'].transform('sum')

            # Calculate proportions
            grouped['proportion'] = grouped['counts'] / total_counts

            sns.set_theme(style="ticks",
                          rc={'figure.figsize': (15, 18)},
                          font_scale=2)
            sns.set_style("ticks")
            ax = sns.histplot(
                grouped,
                y="tech_vul",
                hue="set",
                weights='proportion',
                multiple="stack",
                palette='colorblind',
                edgecolor=".3",
                linewidth=1.0,
                log_scale=True,
            )
            ax.set_xticklabels(ax.get_xticklabels(), rotation=90)
            # Adding labels on each bar
            for p in ax.patches:
                # Get information from the patch
                height = p.get_height()
                width = p.get_width()
                x = p.get_x()
                y = p.get_y()

                # Format label text
                label_text = f'{width:.2f}'

                # Place text at the end of the bar
                ax.text(x + width/2, y + height / 2, label_text,
                        ha='center', va='center', fontsize=20)

            ax.set_xlabel('Proportion', fontsize=30)
            ax.set_ylabel('Technique/Vulnerability', fontsize=30)
            plt.tick_params(axis='x', labelsize=20, rotation=0)
            ylim = ax.get_ylim()
            new_ylim = (ylim[0] - 0.85, ylim[1]+0.85)
            ax.set_ylim(new_ylim)
            ax.set_xlim(0, 1)
            ax.spines[['right', 'top']].set_visible(False)

            plt.tight_layout()
            plt.savefig('dataset_split_distribution.png', dpi=500)

        return train, valid, test


class LoadOtherDataset:
    def __init__(self, file_name):
        self.df = self.import_data(file_name)

    def import_data(sel, file_name):
        with open(file_name, 'r', newline='', encoding='utf-8') as infile:
            content = csv.reader(infile, delimiter=',', quoting=csv.QUOTE_MINIMAL)
            data = []
            columns = None
            for idx, row in enumerate(content):
                if idx == 0:
                    columns = row
                else:
                    data.append(row)
        return pd.DataFrame(data, columns=columns)
