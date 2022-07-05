import gspread    
import xmlrpc.client
import pandas as pd
import numpy as np
import os
import json
import datetime

def Create_Sale_order(request):
    """
    Creating the sale order in Odoo by extracting data from QuickBooks using webhooks and cross reference table in Google Sheets.

    Parameters
    ----------
    request: HTTP request
    request contains the sale id of the order in Quickbooks.

    """
 
    gc = gspread.service_account_from_dict(credentials)
    
    wks = gc.open('xRef')
    
    worksheet = wks.worksheet('Main')
    worksheet2 = wks.worksheet('TGCustomers')

    df = pd.DataFrame(worksheet.get_all_records())
    df2 = pd.DataFrame(worksheet2.get_all_records())

    req = request.get_json()['object_id']

    order_try = req
    get_order = f'curl -X GET -H "Content-type: application/json" -H "Authorization: Bearer ?" https://api.tradegecko.com/orders/{order_try}'
    stream = os.popen(get_order)
    order = stream.readline()
    last_order = json.loads(order)['order']

    channel = last_order['source_id']
    
    order_line_ids = last_order['order_line_item_ids']
    partner_,delivery_date = last_order['company_id'],last_order['ship_at']
    order_line_ids
    reference = last_order['reference_number']
    price_unit = []
    qty = []
    variant_id = []
    if(delivery_date != None):
        element = datetime.datetime.strptime(delivery_date,"%Y-%m-%d")
        delivery_date = str(element + datetime.timedelta(hours = 4))
        
    source_doc = f"https://commerce.intuit.com/orders/{req}"
    if(models.execute_kw(db, uid, password, 'sale.order', 'search_read', [[['origin','=', source_doc]]], {'fields': []}) != []):
        return('Already exist')

    for i in range(len(order_line_ids)):
        
        get_order_lines = f'curl -X GET -H "Content-type: application/json" -H "Authorization: Bearer ?" https://api.tradegecko.com/order_line_items/{order_line_ids[i]}'
        stream_2 = os.popen(get_order_lines)
        order_line_ = stream_2.readline()
        order_line = json.loads(order_line_)["order_line_item"]
        price_unit.append(order_line['price'])
        qty.append(order_line['quantity'])
        variant_id.append(order_line['variant_id'])

    product_id = variant_id
    qty = np.array(qty)
    qty = qty.astype(float)
    price_unit = np.array(price_unit).astype(float)
    qty_ = []
    prod_=[]
    pack=[]
    prod_try = []
    qty_try = []
    qty_res = []
    price_unit_ = []

    for i in range(len(product_id)):
        for j in range(df.shape[0]):
            if(df['TG Variant ID'][j] == product_id[i]):
                prod_.append(df['Odoo ID'][j])
                qty_.append(df['QTY in case'][j])
                pack.append(df['Package Id'][j])
                prod_try.append(product_id[i])
                qty_try.append(qty[i])
                qty_res.append(qty[i] * df['QTY in case'][j]) 
                price_unit_.append(price_unit[i]/df['QTY in case'][j])

    if(len(product_id) != len(prod_try)):
        miss_ = str(list(set(product_id) - set(prod_try)))
        raise ValueError(f"Miss prod_id {miss_} in order : {req} (TradeGecko cross.ref)")

    if (partner_ == 50371489):
        return "1"
    try:    
        partner = df2[df2['/companies/id'] == partner_]['Odoo ID'].values[0]
    except:
        raise ValueError(f"Miss customer id {partner_} in order : {req} (TradeGecko cross.ref)")

    order_lines_params = []
    hard_order_lines = []
    for i in range(len(prod_)):
        if(pack[i] == ''):
            order_line_params = {
                'product_id' : int(prod_[i]),
                'product_uom_qty': float(qty_res[i]),
                'price_unit' : float(price_unit_[i])
                                }
        else:
            order_line_params = {
                'product_id' : int(prod_[i]),
                'product_packaging_id': int(pack[i]),
                'product_uom_qty': float(qty_res[i]),
                'price_unit' : float(price_unit_[i])
                                }
        order_lines_params.append(order_line_params)
        hard_order_lines.append((0,0,order_lines_params[i]))
        
    if(reference==None):
        reference = ''

    
    order_params = {'company_id': 1,
        'warehouse_id': 1,
        'partner_id' : int(partner),
        'client_order_ref' : reference,
        'origin' : source_doc,
        'order_line': hard_order_lines
        }

    if(delivery_date != None): 
        order_params['commitment_date'] = delivery_date

    if(channel == 3718):
        order_params['tag_ids'] = [1,2]
    else:
        order_params['tag_ids'] = [2]

    ord_id = models.execute_kw(db, uid, password, 'sale.order', 'create', [order_params])
    models.execute_kw(db, uid, password, 'sale.order', 'action_confirm', [ord_id])

