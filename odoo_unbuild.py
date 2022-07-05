import xmlrpc.client
import numpy as np

def Odoo_Unbuild(request):
  
    """
    Unbuild the product in the manufacturing order, taking into account child orders and warnings that may appear.

    Parameters
    ----------
    request: HTTP request
    request contains quantity that need to unbuild and unique production_record 

    """

    req = request.get_json()
    new_qty = req['Quantity Produced']
    production_record = req['Production Result ID']

    if(type(new_qty) == str and new_qty.find(',') == True):
        new_qty = float(new_qty.replace(',', ''))
    else:
        new_qty = float(new_qty)

    prod = models.execute_kw(db, uid, password, 'mrp.production', 'search_read', [[['product_description_variants','=', production_record]]],{'fields': []})

    if(prod != [] and prod[-1]['unbuild_count'] < 1 and new_qty != prod[-1]['qty_producing']):

        prod_name = prod[-1]['name']
        prod_id = prod[-1]['id']
        prod_product = prod[-1]['product_id'][0]
        prod_product_uom = prod[-1]['product_uom_id'][0]
        qty_produced = prod[-1]['qty_producing']

        prod_bom = models.execute_kw(db, uid, password, 'product.product', 'search_read', [[['id','=', prod_product]]],{'fields': ['bom_ids','uom_id']})
        bom_id = prod_bom[0]['bom_ids'][0]

        unbuild_params = {
              'mo_id' : prod_id,
              'product_qty' : qty_produced,
              'product_id' : prod_product,
              'product_uom_id' : prod_product_uom,
              'location_id' : 8,
              'location_dest_id' : 8,
              'bom_id' : bom_id
        }


        unbuild = models.execute_kw(db, uid, password, 'mrp.unbuild', 'create', [unbuild_params])

        warning_params = {
            'product_id': prod_product,
            'location_id': 8,
            'quantity': qty_produced,
            'product_uom_name': prod_product_uom,
            'unbuild_id':  unbuild
        }

        try:
            warning = models.execute_kw(db, uid, password, 'stock.warn.insufficient.qty.unbuild', 'create', [warning_params])
            models.execute_kw(db, uid, password, 'stock.warn.insufficient.qty.unbuild', 'action_done', [warning]) 
        except:
            models.execute_kw(db, uid, password, 'mrp.unbuild', 'action_validate', [unbuild])


        prod_child = models.execute_kw(db, uid, password, 'mrp.production', 'search_read', [[['origin','=', prod_name]]],{'fields': []})

        if(prod_child != []):

            prod_child_name = prod_child[0]['name']
            prod_child_id = prod_child[0]['id']

            if(prod_child[0]['state'] == 'done'):

                prod_child_product = prod_child[0]['product_id'][0]
                prod_child_product_uom = prod_child[0]['product_uom_id'][0]
                qty_child_produced = prod_child[0]['qty_producing']

                prod_child_bom = models.execute_kw(db, uid, password, 'product.product', 'search_read', [[['id','=', prod_child_product]]],{'fields': ['bom_ids','uom_id']})
                bom_child_id = prod_child_bom[0]['bom_ids'][0]

                unbuild_child_params = {
                      'mo_id' : prod_child_id,
                      'product_qty' : qty_child_produced,
                      'product_id' : prod_child_product,
                      'product_uom_id' : prod_child_product_uom,
                      'location_id' : 8,
                      'location_dest_id' : 8,
                      'bom_id' : bom_child_id
                }


                unbuild_child = models.execute_kw(db, uid, password, 'mrp.unbuild', 'create', [unbuild_child_params])
                models.execute_kw(db, uid, password, 'mrp.unbuild', 'action_validate', [unbuild_child]) 

            prod_child_pres = models.execute_kw(db, uid, password, 'mrp.production', 'search_read', [[['origin','=', prod_child_name]]],{'fields': []})

            if(prod_child_pres != [] and prod_child_pres[0]['state'] == 'done'):

                prod_child_pres_name = prod_child_pres[0]['name']
                prod_child_pres_id = prod_child_pres[0]['id']
                prod_child_pres_product = prod_child_pres[0]['product_id'][0]
                prod_child_pres_product_uom = prod_child_pres[0]['product_uom_id'][0]
                qty_child_pres_produced = prod_child_pres[0]['qty_producing']

                prod_child_pres_bom = models.execute_kw(db, uid, password, 'product.product', 'search_read', [[['id','=', prod_child_pres_product]]],{'fields': ['bom_ids','uom_id']})
                bom_child_pres_id = prod_child_pres_bom[0]['bom_ids'][0]

                unbuild_child_pres_params = {
                      'mo_id' : prod_child_pres_id,
                      'product_qty' : qty_child_pres_produced,
                      'product_id' : prod_child_pres_product,
                      'product_uom_id' : prod_child_pres_product_uom,
                      'location_id' : 8,
                      'location_dest_id' : 8,
                      'bom_id' : bom_child_pres_id
                }


                unbuild_child_pres = models.execute_kw(db, uid, password, 'mrp.unbuild', 'create', [unbuild_child_pres_params])

                if(prod_child[0]['state'] != 'done'):

                    warning_child_pres_params = {
                        'product_id': prod_child_pres_product,
                        'location_id': 8,
                        'quantity': qty_child_pres_produced,
                        'product_uom_name': prod_child_pres_product_uom,
                        'unbuild_id':  unbuild_child_pres
                    }

                    try:
                        warning_child_pres = models.execute_kw(db, uid, password, 'stock.warn.insufficient.qty.unbuild', 'create', [warning_child_pres_params])
                        models.execute_kw(db, uid, password, 'stock.warn.insufficient.qty.unbuild', 'action_done', [warning_child_pres]) 
                    except:
                        models.execute_kw(db, uid, password, 'mrp.unbuild', 'action_validate', [unbuild_child_pres])

                else:
                    models.execute_kw(db, uid, password, 'mrp.unbuild', 'action_validate', [unbuild_child_pres]) 

