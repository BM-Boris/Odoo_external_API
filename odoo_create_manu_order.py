def Odoo_Create_Manu_order(request):

    """
    Creating the manufacturing order in Odoo and reservation of product to futher packaging.

    Parameters
    ----------
    request: HTTP request
    request contains produced quantity, unique production_record, product id and sale order id

    """

    req = request.get_json()
    product_id = req['Product ID']
    qty_produced = req['Quantity Produced']
    production_record = req['Production Result ID']

    if(type(product_id) == str and product_id.find(',') == True):
        product_id = int(product_id.replace(',', ''))
    else:
        product_id = int(product_id)

    if(type(qty_produced) == str and qty_produced.find(',') == True):
        qty_produced = float(qty_produced.replace(',', ''))
    else:
        qty_produced = float(qty_produced)

    if (models.execute_kw(db, uid, password, 'mrp.production', 'search_read',
                          [[['product_description_variants', '=', production_record]]],
                          {'fields': []}) == []):

        
        #Id Recepie

        bom_ = models.execute_kw(db, uid, password, 'product.product', 'search_read', [[['id','=', product_id]]],{'fields': ['bom_ids','uom_id']})[0]
        bom_id = bom_['bom_ids'][0]
        uom_id = bom_['uom_id'][0]

        #Ingredients

        list_bom_keys = models.execute_kw(db, uid, password, 'mrp.bom.line', 'search_read', [[['bom_id','=', bom_id]]], {'fields': ["product_id", "product_qty", "product_uom_id"]})
        bom_product_id = [i['product_id'] for i in list_bom_keys] 
        bom_product_qty = [i['product_qty'] for i in list_bom_keys] 
        bom_product_uom_id = [i['product_uom_id'] for i in list_bom_keys] 
        bom_product_id = [i[0] for i in bom_product_id]
        bom_product_uom_id = [i[0] for i in bom_product_uom_id]
        bom_ids = [i['id'] for i in list_bom_keys]

        bom_ = models.execute_kw(db, uid, password, 'mrp.bom', 'search_read', [[['id','=', bom_id]]], {'fields': ["product_qty"]})[0]
        bom_qty = bom_['product_qty']

        move_ingreds_params = []
        hard_move_ingred = []
        raw_qty = []

        #Ingredients Move Dict

        for i in range(len(bom_ids)):

            a = qty_produced*(bom_product_qty[i]/bom_qty)
            a = a*100
            if((a)%1>0):
                a = a+1
                a = (a-a%1)
            a = a/100
            
            raw_qty.append(a)
          
            move_ingred_params = {
                'product_id' : bom_product_id[i],
                'product_uom' : bom_product_uom_id[i],
                'location_id': 8,
                'product_uom_qty' : raw_qty[i]
               }
            move_ingreds_params.append(move_ingred_params)
            hard_move_ingred.append((0,0,move_ingreds_params[i]))
        
        #Product Dict
        man_order_params = {'product_id' : product_id,
                'product_qty' : qty_produced,
                'bom_id' : bom_id,
                'product_uom_id' : uom_id,
                'product_description_variants' : production_record,
                'move_raw_ids' : hard_move_ingred,
            }

        #Create Man. Order and Ingred. move(move_raw_ids)

        man_id = models.execute_kw(db, uid, password, 'mrp.production', 'create', [man_order_params])
        models.execute_kw(db, uid, password, 'mrp.production', 'action_confirm', [man_id])


        #Product Move Dict
        
        move_params = {
                'product_id' : product_id,
                'product_uom' : uom_id,
                'location_id' : 15,
                'location_dest_id' : 8,
                'production_id' : man_id
        }

        #Create product move('move_finished_ids')

        move_ = models.execute_kw(db, uid, password, 'stock.move', 'create', [move_params])

        #Update the QTY

        for i in range(len(bom_ids)):
            move_raw_ids = models.execute_kw(db, uid, password, 'mrp.production', 'search_read', [[['id','=', man_id]]],{'fields': ['move_raw_ids']})[0]['move_raw_ids'][i]
            models.execute_kw(db, uid, password, 'stock.move', 'write', [move_raw_ids, {'quantity_done' : float(raw_qty[i])}])
            
        models.execute_kw(db, uid, password, 'mrp.production', 'write', [man_id, {'qty_producing' : qty_produced}])

        #Mark it Done
        models.execute_kw(db, uid, password, 'mrp.production', 'button_mark_done', [man_id])

        sale_id = req['SO ID']

        if(type(sale_id) == str and sale_id.find(',') == True):
            sale_id = int(sale_id.replace(',', ''))
        elif(sale_id == ''):
            sale_id = ''
        else:
            sale_id = int(sale_id)


        if(sale_id != ''):
            
            pick_id = models.execute_kw(db, uid, password, 'stock.picking', 'search_read', [[['sale_id','=', sale_id], ['picking_type_id','=', 3]]],{'fields': ['id']})[0]['id']
            
            try:
                models.execute_kw(db, uid, password, 'stock.picking', 'action_assign', [pick_id]) 
            except:
                pass
