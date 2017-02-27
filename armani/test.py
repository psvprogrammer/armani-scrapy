
import pandas as pd
import json


def get_color_size_fill(df):
    color_items, size_items, desc_items = 0.0, 0.0, 0.0
    total = float(len(set(df['sku'])))
    for sku in set(df['sku']):
        sku_filter = df[df['sku'].isin([sku])]
        if len(set(sku_filter['color'])) > 1:
            color_items += 1
        if len(set(sku_filter['size'])) > 1:
            size_items += 1

    for ind, row in df.iterrows():
        if row['description'].strip() != '':
            desc_items += 1

    color_fill = color_items / total * 100
    size_fill = size_items / total * 100
    desc_fill = desc_items / len(df) * 100

    return color_fill, size_fill, desc_fill


def run_test():
    df = pd.read_csv('../main_items.csv')
    item_total = len(df)
    if len(set(df['currency'])) == 1 and df['currency'][1] == '$':
        currency = 'currency is correct ($)'
    else:
        currency = 'wrong currency'

    color_fill, size_fill, desc_fill = get_color_size_fill(df)

    result = {
        'Total items scraped': item_total,
        'Currency': currency,
        'Color variety': '{0:.2f}'.format(color_fill),
        'Size variety': '{0:.2f}'.format(size_fill),
        'Description variety': '{0:.2f}'.format(desc_fill),
    }

    with open('armani_test_result.json', 'w') as file:
        json.dump(result, file)

if __name__ == '__main__':
    run_test()
