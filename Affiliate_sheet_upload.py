class AffliateOrderExcelUpload(APIView):
    authentication_classes = (JWTTokenAuthentication,)

    def post(self,request):
        if settings.DEBUG_CONF:
            file_path = "/var/www/excels-copy/affiliate-excels/"
        else:
            file_path = "/var/www/excels-copy/affiliate-excels/"
        current_time = get_db_datetime()
        try:
            current_sheet = request.data["attachments"]
            affiliate_id = int(request.data["affiliate_id"])
            upload_by_id = request.user['login_id']
            role_type = request.user['role']
            upload_by = request.user['email']
        except:
            return Response({"message": "Invalid data given."},
                status=status.HTTP_404_NOT_FOUND)
        if 'OPS' not in role_type:
            msg = "Invalid role"
            return Response(
                {'error': msg},
                status=status.HTTP_403_FORBIDDEN)
        order_id = set()
        cet_id = 0
        sheet_name = CONST.PLATFORM_DICT.get(affiliate_id, '').upper()
        file_name_format =\
            current_time.strftime(
                f"UPLOADED-{sheet_name}-SHEET-%Y%m%d-%H%M") + "." + "xlsx"
        file_name =\
            upload_excel_sheet(
                current_sheet, file_path, file_name_format)
        if file_name is None:
            msg = 'File type or path is invalid'
            return Response(
                {"message": msg},
                    status=status.HTTP_400_BAD_REQUEST)

        now = get_db_datetime()
        if affiliate_id==1001:
            # pd.pandas.set_option('display.max_colwidth', None)
            # pd.pandas.set_option('display.max_columns', None)
            fba_fin_path = file_path + file_name
            fin_fba = pd.read_excel(fba_fin_path)
            fin_fba.fillna('', inplace=True)

            successful_count_for_forward_data = 0
            successful_count_for_return_data = 0
            existing_invoice_no_list = []
            message = {
                "success_count_for_forward_data": successful_count_for_forward_data,
                "success_count_for_return_data": successful_count_for_return_data,
                "existing_cart_ids": existing_invoice_no_list,
                "failed_cart_ids": []
            }
        else:
            wb_obj = openpyxl.load_workbook(file_path + file_name)
            sheet_obj = wb_obj.active
            m_row = sheet_obj.max_row
            m_col = sheet_obj.max_column
            failed_cart_id_list = []
            successfull_count = 0
            total_orders = 0
            existing_cart_id_list = []
            affiliate_order_list = []
            new_affiliate_sku_list = []
            promised_edd = None
            promised_dispatch_timestamp = None
            current_dispatch_timestamp = None
            estimated_dispatch_log = ''
            estimated_delivery_log = ''
            estimated_delivery_timestamp = None
            edd_list = []
            message = {
                "success_count": successfull_count,
                "existing_cart_ids": existing_cart_id_list,
                "failed_cart_ids": failed_cart_id_list
            }

        if affiliate_id == 1:
            try:
                aff_sheet = WfAffiliateSheetUploads.objects.create(
                    affiliate_id=1,
                    sheet_name=file_name_format,
                    upload_by=upload_by,
                    upload_by_id=upload_by_id,
                    created_timestamp=now,
                    is_active=1
                )
            except Exception as e:
                print(e, "Exception in creation of sheet upload row")
                msg = 'Error in creation of sheet upload row'
                return Response(
                    {"error": msg},
                    status=status.HTTP_400_BAD_REQUEST)
            sheet_upload_id = aff_sheet.id
            for row in range(2, m_row+1):
                hold_reason_id = 0
                try:
                    affiliate_order_id =\
                        sheet_obj.cell(
                            row = row, column=column_index_from_string('A')).value
                    if affiliate_order_id is None:
                        continue
                    total_orders += 1
                    order_random_id =\
                        sheet_obj.cell(
                            row = row, column=column_index_from_string('A')).value.strip()
                    cart_id1 =\
                        sheet_obj.cell(
                            row = row, column=column_index_from_string('B')).value
                    cart_id = str(cart_id1).split(".")[0].strip()
                    order_exist =\
                        check_existing_affiliate_order(
                            cart_id, affiliate_id=1)
                    if order_exist:
                        existing_cart_id_list.append(cart_id)
                        continue
                    affiliate_sku =\
                        sheet_obj.cell(
                            row = row, column=column_index_from_string('H')).value
                    item_sku =\
                        sheet_obj.cell(
                            row = row, column=column_index_from_string('H')).value.strip()
                    item_name =\
                        sheet_obj.cell(
                            row = row, column=column_index_from_string('I')).value
                    item_quantity =\
                        sheet_obj.cell(
                            row = row, column=column_index_from_string('J')).value
                    item_price =\
                        sheet_obj.cell(
                            row = row, column=column_index_from_string('L')).value
                    orm_order_status = 1
                    firstname =\
                        sheet_obj.cell(
                            row = row, column=column_index_from_string('F')).value
                    lastname = ''
                    email_address =\
                        sheet_obj.cell(
                            row = row, column=column_index_from_string('E')).value
                    mobile_number1 =\
                        sheet_obj.cell(
                            row = row, column=column_index_from_string('G')).value
                    mobile_number = mobile_number1 if mobile_number1 else ''
                    mobile_number =\
                        str(mobile_number).split('.')[0].replace(' ','')
                    alternate_mobile_number1 =\
                        sheet_obj.cell(
                            row = row, column=column_index_from_string('Y')).value
                    alternate_mobile_number =\
                        alternate_mobile_number1 if alternate_mobile_number1 else ''
                    alternate_mobile_number =\
                        str(alternate_mobile_number).split('.')[0].replace(' ','')
                    address1 =\
                        sheet_obj.cell(
                            row = row, column=column_index_from_string('R')).value
                    address2 = address1 if address1 else ''
                    address3 =\
                        sheet_obj.cell(
                            row = row, column=column_index_from_string('S')).value
                    address4 = address3 if address3 else ''
                    address = f'{address2},{address4}'
                    landmark = ''
                    pincode =\
                        sheet_obj.cell(
                            row = row, column=column_index_from_string('W')).value
                    pincode = int(pincode)
                    ship_service_level =\
                        sheet_obj.cell(
                            row = row, column=column_index_from_string('P')).value
                    city =\
                        sheet_obj.cell(
                            row = row, column=column_index_from_string('U')).value
                    state =\
                        sheet_obj.cell(
                            row = row, column=column_index_from_string('V')).value
                    estimate_delivery = ''
                    create_timestamp =\
                        sheet_obj.cell(
                            row = row, column=column_index_from_string('C')).value
                    create_timestamp = utc_time_to_ist(create_timestamp)
                    promised_dispatch_timestamp =\
                        sheet_obj.cell(
                            row = row, column=column_index_from_string('AI')).value
                    promised_dispatch_timestamp = utc_time_to_ist(promised_dispatch_timestamp)
                    promised_edd =\
                        sheet_obj.cell(
                            row = row, column=column_index_from_string('AK')).value
                    promised_edd = utc_time_to_ist(promised_edd)
                    #create_timestamp = current_time
                    order_confirmed_on = None
                    is_an_accessory =\
                        Product.check_product_an_accessory(Product.get_type_from_sku(item_sku=item_sku))
                    if is_an_accessory:
                        order_confirmed_on = create_timestamp
                        orm_order_status = OrmStatus.CONFIRMED
                    pincode_detail =\
                        get_city_state_edd_by_pincode(pincode)
                    if pincode_detail:
                        city = pincode_detail['city']
                        state = pincode_detail['state']
                        estimate_delivery = pincode_detail['edd']
                    else:
                        if not is_an_accessory:
                            order_confirmed_on = None
                        orm_order_status = 14
                        hold_reason_id = int(HoldReasonID.NON_SERVICABLE_PINCODE)
                        msg = f'for order_id {order_random_id} pincode {pincode} is'\
                            f' not in delivery sheet/database.Hence'\
                                f' Order moved on hold'
                        failed_cart_id_list.append(msg)
                        #continue
                    wf_sku = get_wf_mapped_skucode(affiliate_sku)
                    if wf_sku:
                        item_sku = wf_sku
                    else:
                        new_affiliate_sku_list.append(f'{order_random_id}: {item_sku}')
                    if isinstance(item_price, str):
                        item_price = float(item_price)
                    if item_sku.startswith('WFBM'):
                        item_skus = []
                        sku_dimensions = [item_sku[-4:]][0]
                        item_skus.append("WSWB"+sku_dimensions+"-COMBO")
                        item_skus.append("WOMFM-COMBO-"+sku_dimensions+"6")
                        item_prices = ['12000']
                        item_prices.append(round(item_price-12000))
                        item_dimensions = ['78x72 inch', '78x72x6 inch']
                        if sku_dimensions == '7860':
                            item_prices =\
                                list(['11000', round(item_price-12000)])
                            item_dimensions =\
                                list(['78x60 inch','78x60x6 inch'])
                        if round(item_price) <= 10999:
                            item_prices =\
                                list(['5999', round(item_price-5999)])
                    elif item_sku.startswith('WSMRC'):
                        item_skus = [item_sku]
                        id_check, id_dimension = Product.get_item_dimension_from_sku(item_sku)
                        item_dimensions = id_dimension if id_check else ''
                        item_dimensions = [item_dimensions]
                        item_prices =\
                            [str(round(int(item_price)/int(item_quantity)))]
                    else:
                        if item_sku.startswith('COPYWDCM'):
                            item_sku = item_sku.replace('COPYWDCM', 'WDCM')
                        elif item_sku.startswith('WFP'):
                            item_sku = item_sku.replace(item_sku, 'WMFP')
                        item_dimensions =\
                            [Product.get_item_sku_dimensions(item_sku)]
                        item_skus = [item_sku]
                        item_prices =\
                            [str(round(int(item_price)/int(item_quantity)))]
                    item_sku_len = len(item_skus)
                    for i in range(item_sku_len):
                        affiliate_obj = WfAffiliateOrders()
                        affiliate_obj.sheet_upload_id = sheet_upload_id
                        affiliate_obj.affiliate_id = 1
                        affiliate_obj.payment_type = "ECOM"
                        affiliate_obj.affiliate_order_id = affiliate_order_id
                        affiliate_obj.order_random_id = order_random_id
                        affiliate_obj.cart_id = cart_id
                        affiliate_obj.affiliate_sku = affiliate_sku
                        affiliate_obj.item_sku = item_skus[i]
                        affiliate_obj.item_name = item_name
                        affiliate_obj.item_dimensions = item_dimensions[i]
                        affiliate_obj.item_quantity = item_quantity
                        affiliate_obj.item_price = item_prices[i]
                        if pincode and orm_order_status == OrmStatus.NEW_ORDER.value and \
                            is_valid_phone_number(get_corrected_mobile_number(mobile_number)):
                            order_confirmed_on = create_timestamp
                            if Product.is_standard_product(item_skus[i]):
                                orm_order_status = OrmStatus.CONFIRMED
                            else:
                                orm_order_status = OrmStatus.CONFIRMED_WITH_CUSTOMIZATION
                        affiliate_obj.orm_order_status = orm_order_status
                        affiliate_obj.hold_reason_id = hold_reason_id
                        affiliate_obj.firstname = firstname
                        affiliate_obj.lastname = lastname
                        affiliate_obj.email_address = email_address
                        affiliate_obj.mobile_number = mobile_number
                        affiliate_obj.alternate_mobile_number =\
                            alternate_mobile_number
                        affiliate_obj.address = address
                        # gst_extract_result = gst_extract(address)
                        # if gst_extract_result:
                        #     affiliate_obj.gst_number = gst_extract_result
                        affiliate_obj.landmark = landmark
                        affiliate_obj.pincode = pincode
                        affiliate_obj.ship_service_level = ship_service_level
                        affiliate_obj.city = city
                        affiliate_obj.state = state
                        affiliate_obj.estimate_delivery = estimate_delivery
                        sku_code = Product.get_sku_code(item_skus[i])
                        is_standard_product = 1
                        if sku_code in CONST.MATTRESS_SKUS:
                            is_standard_product = Product.get_is_standard_product_size(item_skus[i])
                        affiliate_obj.is_standard_product_size = is_standard_product
                        affiliate_obj.cet_id = cet_id
                        affiliate_obj.create_timestamp = create_timestamp
                        affiliate_obj.update_timestamp = now
                        affiliate_obj.order_confirmed_on = order_confirmed_on
                        affiliate_obj.promised_dispatch_timestamp = promised_dispatch_timestamp
                        affiliate_obj.promised_edd = promised_edd
                        affiliate_order_list.append(affiliate_obj)
                        order_id.add(order_random_id)
                        edd_list.append([cart_id, item_skus[i], pincode, item_quantity])
                    successfull_count += 1

                except Exception as e:
                    print(e, "Exception in converting amazon order " + str(order_random_id))
                    logger.error(e, "Exception in converting amazon order " + str(order_random_id))
                    failed_cart_id_list.append(order_random_id)
                    continue
            try:
                if len(affiliate_order_list) != 0:
                    list_of_object_affiliate_orders = WfAffiliateOrders.objects.bulk_create(affiliate_order_list)
                    message['success_count'] = successfull_count
                    if settings.DEBUG_CONF:
                        assign_order_cet_and_sent_notification(list(order_id), 1)
                    else:
                        assign_order_cet_and_sent_notification.apply_async(args=[list(order_id), 1])
                for order in affiliate_order_list:
                    try:
                        # TwoFcShippingLabel.generate_shipping_label(order.order_random_id)
                        assign_estmiated_warehouse([order.cart_id])
                        assign_shipping_label_to_order.apply_async(args=[order.order_random_id])
                    except Exception as e: # TODO-Abhinav handle log
                        logger.error(f'Exception in generating shipping label : {e}', exc_info=True )
                        pass
                    # assign_shipping_label_to_order.apply_async(args=[order.order_random_id])
                    if order.orm_order_status == OrmStatus.CONFIRMED:
                        sent_email_sms_notification.apply_async(
                            args=[StatusType.CONFIRMED, None, order.order_random_id, {}, 1])
                    elif order.orm_order_status == OrmStatus.CONFIRMED_WITH_CUSTOMIZATION:
                        sent_email_sms_notification.apply_async(
                            args=[StatusType.CONFIRMED, None, order.order_random_id, {}, 1])
                    # edd_affiliate_order.apply_async(args=[edd_list, 1])
                if len(new_affiliate_sku_list) != 0:
                    mail_title = 'Amazon New SKU Code'
                    mail_body = f'New_Sku-{new_affiliate_sku_list}'
                    email_to = ['tech-team@wakefit.co']
                    send_mail_only.apply_async(args=[mail_title, mail_body, email_to, [], []])
                WfAffiliateSheetUploads.objects.filter(
                    id=sheet_upload_id).update(
                        total_orders=total_orders,
                        new_orders=successfull_count,
                        failed_orders=tuple(failed_cart_id_list) if failed_cart_id_list else ''
                    )
                s3_path = f'excels-copy/affiliate-excels/{file_name}'
                upload_file_s3(file_path + file_name, s3_path, True)

            except Exception as e:
                print(e, "Error in bulk create amazon orders")
                message['success_count'] = 0
                message['failed_cart_ids'] = order_id
                mail_title = '[Error Amazon Excel Upload]'
                mail_body = f'Error is bulk create amazon orders'
                exec_str = str(traceback.format_exc())
                send_error_mail.apply_async(args=[mail_title, mail_body, str(e), exec_str])
            return Response(
                {"message": message},
                status=status.HTTP_200_OK)


        elif affiliate_id == 3:

            try:
                aff_sheet = WfAffiliateSheetUploads.objects.create(
                    affiliate_id=3,
                    sheet_name=file_name_format,
                    upload_by=upload_by,
                    upload_by_id=upload_by_id,
                    created_timestamp=now,
                    is_active=1
                )
            except Exception as e:
                print(e, "Exception")
                msg = 'Error in creation of sheet upload row'
                return Response(
                    {"error": msg},
                    status=status.HTTP_400_BAD_REQUEST)
            sheet_upload_id = aff_sheet.id
            for row in range(2, m_row+1):
                hold_reason_id = 0
                try:
                    affiliate_order_id =\
                        sheet_obj.cell(
                            row = row, column=column_index_from_string('E')).value
                    if affiliate_order_id is None:
                        continue
                    total_orders += 1
                    order_random_id =\
                        sheet_obj.cell(
                            row = row, column=column_index_from_string('E')).value.strip()
                    # Remove ',' from cart_id
                    cart_id1 =\
                        sheet_obj.cell(
                            row = row, column=column_index_from_string('F')).value
                    if type(cart_id1) not in [int, float]:
                        cart_id = str(cart_id1).replace("'", '').strip()
                    else:
                        cart_id = cart_id1
                    cart_id = int(cart_id)
                    order_exist =\
                        check_existing_affiliate_order(
                            cart_id, affiliate_id=3)
                    if order_exist:
                        existing_cart_id_list.append(cart_id)
                        continue
                    affiliate_sku =\
                        sheet_obj.cell(
                            row = row, column=column_index_from_string('H')).value
                    location_id =\
                        sheet_obj.cell(
                            row = row, column=column_index_from_string('AL')).value  #Last Column
                    item_sku =\
                        sheet_obj.cell(
                            row = row, column=column_index_from_string('H')).value.strip()
                    item_name =\
                        sheet_obj.cell(
                            row = row, column=column_index_from_string('C')).value
                    item_dimensions = ''
                    item_quantity =\
                        sheet_obj.cell(
                            row = row, column=column_index_from_string('L')).value
                    item_price =\
                        sheet_obj.cell(
                            row = row, column=column_index_from_string('O')).value
                    orm_order_status = 1
                    firstname =\
                        sheet_obj.cell(
                            row = row, column=column_index_from_string('T')).value
                    lastname = ''
                    email_address1 =\
                        sheet_obj.cell(
                            row = row, column=column_index_from_string('AB')).value
                    email_address = email_address1 if email_address1 else ''
                    mobile_number1 =\
                        sheet_obj.cell(
                            row = row, column=column_index_from_string('AA')).value
                    mobile_number = mobile_number1 if mobile_number1 else ''
                    mobile_number =\
                        str(mobile_number).split('.')[0].replace(' ','')
                    alternate_mobile_number = ''
                    address =\
                        sheet_obj.cell(
                            row = row, column=column_index_from_string('V')).value
                    landmark1 =\
                        sheet_obj.cell(
                            row = row, column=column_index_from_string('W')).value
                    landmark = landmark1 if landmark1 else ''
                    pincode =\
                        sheet_obj.cell(
                            row = row, column=column_index_from_string('Z')).value
                    pincode = int(pincode)
                    ship_service_level = None
                    city =\
                        sheet_obj.cell(
                            row = row, column=column_index_from_string('X')).value
                    state =\
                        sheet_obj.cell(
                            row = row, column=column_index_from_string('Y')).value
                    promised_dispatch_timestamp1 =\
                        sheet_obj.cell(
                            row = row, column=column_index_from_string('AD')).value
                    if type(promised_dispatch_timestamp1) != datetime:
                        now = datetime.strptime(promised_dispatch_timestamp1, '%b %d, %Y %H:%M:%S')
                        promised_dispatch_timestamp = timezone.make_aware(now)
                    else:
                        promised_dispatch_timestamp = timezone.make_aware(promised_dispatch_timestamp1)
                    promised_edd1 =\
                        sheet_obj.cell(
                            row = row, column=column_index_from_string('AF')).value
                    if type(promised_edd1) != datetime:
                        now = datetime.strptime(promised_edd1, '%b %d, %Y %H:%M:%S')
                        promised_edd = timezone.make_aware(now)
                    else:
                        promised_edd = timezone.make_aware(promised_edd1)
                    estimate_delivery = ''
                    create_timestamp1 =\
                        sheet_obj.cell(
                            row = row, column=column_index_from_string('A')).value
                    if type(create_timestamp1) != datetime:
                        now = datetime.strptime(create_timestamp1, '%b %d, %Y')
                        create_timestamp = timezone.make_aware(now)
                    else:
                        create_timestamp = timezone.make_aware(create_timestamp1)
                    order_confirmed_on = None
                    is_an_accessory =\
                        Product.check_product_an_accessory(Product.get_type_from_sku(item_sku=item_sku))
                    if is_an_accessory:
                        order_confirmed_on = create_timestamp
                        orm_order_status = 2
                    pincode_detail =\
                        get_city_state_edd_by_pincode(pincode)
                    if pincode_detail:
                        city = pincode_detail['city']
                        state = pincode_detail['state']
                        estimate_delivery = pincode_detail['edd']
                    else:
                        if not is_an_accessory:
                            order_confirmed_on = None
                        orm_order_status = 14
                        hold_reason_id = int(HoldReasonID.NON_SERVICABLE_PINCODE)
                        msg = f'for order_id {order_random_id} pincode {pincode} is'\
                            f' not in delivery sheet/database.Hence'\
                                f' Order moved on hold'
                        failed_cart_id_list.append(msg)
                        #continue
                    wf_sku = get_wf_mapped_skucode(affiliate_sku)
                    if wf_sku:
                        item_sku = wf_sku
                    else:
                        new_affiliate_sku_list.append(f'{order_random_id}: {item_sku}')
                        item_dimensions, item_sku =\
                            affiliate_sku_code(affiliate_sku, affiliate_id)
                    if item_dimensions == '':
                        item_dimensions = Product.get_item_sku_dimensions(item_sku)
                    affiliate_obj = WfAffiliateOrders()
                    affiliate_obj.sheet_upload_id = sheet_upload_id
                    affiliate_obj.affiliate_id = 3
                    affiliate_obj.payment_type = "ECOM"
                    affiliate_obj.affiliate_order_id = affiliate_order_id
                    affiliate_obj.order_random_id = order_random_id
                    affiliate_obj.cart_id = cart_id
                    affiliate_obj.affiliate_sku = affiliate_sku
                    affiliate_obj.item_sku = item_sku
                    affiliate_obj.item_name = item_name
                    affiliate_obj.item_dimensions = item_dimensions
                    affiliate_obj.item_quantity = item_quantity
                    affiliate_obj.item_price = item_price
                    if pincode and orm_order_status == OrmStatus.NEW_ORDER.value and \
                            is_valid_phone_number(get_corrected_mobile_number(mobile_number)):
                        order_confirmed_on = create_timestamp
                        if Product.is_standard_product(item_sku):
                            orm_order_status = OrmStatus.CONFIRMED
                        else:
                            orm_order_status = OrmStatus.CONFIRMED_WITH_CUSTOMIZATION
                    affiliate_obj.orm_order_status = orm_order_status
                    affiliate_obj.hold_reason_id = hold_reason_id
                    affiliate_obj.firstname = firstname
                    affiliate_obj.lastname = lastname
                    affiliate_obj.email_address = email_address
                    affiliate_obj.mobile_number = mobile_number
                    affiliate_obj.alternate_mobile_number =\
                        alternate_mobile_number
                    affiliate_obj.address = address
                    # gst_extract_result = gst_extract(address)
                    # if gst_extract_result:
                    #     affiliate_obj.gst_number = gst_extract_result
                    affiliate_obj.landmark = landmark
                    affiliate_obj.pincode = pincode
                    affiliate_obj.ship_service_level = ship_service_level
                    affiliate_obj.city = city
                    affiliate_obj.state = state
                    affiliate_obj.estimate_delivery = estimate_delivery
                    sku_code = Product.get_sku_code(item_sku)
                    is_standard_product = 1
                    if sku_code in CONST.MATTRESS_SKUS:
                        is_standard_product = Product.get_is_standard_product_size(item_sku)
                    affiliate_obj.is_standard_product_size = is_standard_product
                    affiliate_obj.cet_id = cet_id
                    affiliate_obj.create_timestamp = create_timestamp
                    affiliate_obj.update_timestamp = now
                    affiliate_obj.order_confirmed_on = order_confirmed_on
                    affiliate_obj.promised_dispatch_timestamp = promised_dispatch_timestamp
                    affiliate_obj.promised_edd = promised_edd
                    if location_id:
                        affiliate_obj.location_id = location_id
                    affiliate_order_list.append(affiliate_obj)
                    order_id.add(order_random_id)
                    edd_list.append([cart_id, item_sku, pincode, item_quantity])
                    successfull_count += 1
                except Exception as e:
                    print(e, "Exception")
                    if order_random_id == 'Order Id':
                        total_orders -= 1
                        continue
                    failed_cart_id_list.append(order_random_id)
                    continue
            try:
                if len(affiliate_order_list) != 0:
                    list_of_object_affiliate_orders = WfAffiliateOrders.objects.bulk_create(affiliate_order_list)
                    message['success_count'] = successfull_count
                    if settings.DEBUG_CONF:
                        assign_order_cet_and_sent_notification(list(order_id), 3)
                    else:
                        assign_order_cet_and_sent_notification.apply_async(args=[list(order_id), 3])

                    # edd_affiliate_order.apply_async(args=[edd_list, 3])
                for order in affiliate_order_list:
                    try:
                        # TwoFcShippingLabel.generate_shipping_label(order.order_random_id)
                        assign_estmiated_warehouse([order.cart_id])
                        assign_shipping_label_to_order.apply_async(args=[order.order_random_id])
                    except Exception as e: # TODO-Abhinav handle log
                        logger.error(f'Exception in generating shipping label : {e}', exc_info=True )
                        pass
                    # assign_shipping_label_to_order.apply_async(args=[order.order_random_id])
                    if order.orm_order_status == OrmStatus.CONFIRMED:
                        sent_email_sms_notification.apply_async(
                            args=[StatusType.CONFIRMED, None, order.order_random_id, {}, 3])
                    elif order.orm_order_status == OrmStatus.CONFIRMED_WITH_CUSTOMIZATION:
                        sent_email_sms_notification.apply_async(
                            args=[StatusType.CONFIRMED, None, order.order_random_id, {}, 3])
                    # edd_affiliate_order.apply_async(args=[edd_list, 1])
                if len(new_affiliate_sku_list) != 0:
                    mail_title = 'Flipcart New SKU Code'
                    mail_body = f'New_Sku-{new_affiliate_sku_list}'
                    email_to = ['tech-team@wakefit.co']
                    send_mail_only.apply_async(args=[mail_title, mail_body, email_to, [], []])
                WfAffiliateSheetUploads.objects.filter(
                    id=sheet_upload_id).update(
                        total_orders=total_orders,
                        new_orders=successfull_count,
                        failed_orders=tuple(failed_cart_id_list) if failed_cart_id_list else ''
                    )
                s3_path = f'excels-copy/affiliate-excels/{file_name}'
                upload_file_s3(file_path + file_name, s3_path, True)

            except Exception as e:
                print(e, "Error in bulk create flipcart orders")
                message['success_count'] = 0
                message['failed_cart_ids'] = order_id
                mail_title = 'Error Flipcart Excel Upload'
                mail_body = f'Error in bulk create flipcart orders'
                exec_str = str(traceback.format_exc())
                send_error_mail.apply_async(args=[mail_title, mail_body, str(e), exec_str])
            return Response(
                {"message": message},
                status=status.HTTP_200_OK)


        elif affiliate_id == 2:

            if not CONST.IS_PEPPERFRY_ORDER_ACTIVE:
                msg = 'Currently not accepting pepperfry orders'
                return Response(
                    {"error": msg},
                    status=status.HTTP_400_BAD_REQUEST)

            try:
                aff_sheet = WfAffiliateSheetUploads.objects.create(
                    affiliate_id=2,
                    sheet_name=file_name_format,
                    upload_by=upload_by,
                    upload_by_id=upload_by_id,
                    created_timestamp=now,
                    is_active=1
                )
            except Exception as e:
                print(e, "Exception")
                msg = 'Error in creation of sheet upload row'
                return Response(
                    {"error": msg},
                    status=status.HTTP_400_BAD_REQUEST)
            sheet_upload_id = aff_sheet.id
            for row in range(2, m_row+1):
                hold_reason_id = 0
                try:
                    affiliate_order_id =\
                        sheet_obj.cell(
                            row = row, column=column_index_from_string('A')).value
                    if affiliate_order_id is None:
                        continue
                    total_orders += 1
                    order_random_id = affiliate_order_id.split("_")[0].strip()
                    cart_id =\
                        sheet_obj.cell(
                            row = row, column=column_index_from_string('A')).value.strip()
                    order_exist =\
                        check_existing_affiliate_order(
                            cart_id, affiliate_id=2)
                    if order_exist:
                        existing_cart_id_list.append(cart_id)
                        continue
                    affiliate_sku =\
                        sheet_obj.cell(
                            row = row, column=column_index_from_string('G')).value
                    item_sku = affiliate_sku.split("_")[0].strip()
                    item_name =\
                        sheet_obj.cell(
                            row = row, column=column_index_from_string('F')).value
                    item_dimensions = ''
                    item_quantity =\
                        sheet_obj.cell(
                            row = row, column=column_index_from_string('C')).value
                    item_price =\
                        sheet_obj.cell(
                            row = row, column=column_index_from_string('D')).value
                    promised_dispatch_timestamp = \
                        sheet_obj.cell(
                            row=row, column=column_index_from_string('I')).value
                    if type(promised_dispatch_timestamp) != datetime:
                        now = datetime.strptime(promised_dispatch_timestamp, '%Y-%m-%d')
                        promised_dispatch_timestamp = timezone.make_aware(now)
                    else:
                        promised_dispatch_timestamp = timezone.make_aware(promised_dispatch_timestamp)
                    orm_order_status = 1
                    email_address = ''
                    alternate_mobile_number = ''
                    landmark = ''
                    ship_service_level = None
                    estimate_delivery = ''
                    create_timestamp1 =\
                        sheet_obj.cell(
                            row = row, column=column_index_from_string('H')).value
                    if type(create_timestamp1) != datetime:
                        now = datetime.strptime(create_timestamp1, '%Y-%m-%d')
                        create_timestamp = timezone.make_aware(now)
                    else:
                        create_timestamp = timezone.make_aware(create_timestamp1)
                    customer_detail_string =\
                        sheet_obj.cell(
                            row = row, column=column_index_from_string('K')).value
                    customer_detail_list = customer_detail_string.split("<br/>")
                    if len(customer_detail_list) > 5 and customer_detail_list[-3].isdigit():
                        pincode = customer_detail_list[-3]
                        mobile_number = customer_detail_list[-2]
                    else:
                        pincode = customer_detail_list[-2]
                        mobile_number = customer_detail_list[-1]
                    full_name = customer_detail_list[0]
                    lastname = ''
                    firstname = full_name
                    if full_name:
                        name_split = full_name.split(" ")
                        if len(name_split) > 1:
                            firstname = " ".join(name_split[:-1])
                            lastname = name_split[-1]
                    address = customer_detail_list[1]
                    order_confirmed_on = None
                    is_an_accessory = Product.check_product_an_accessory(Product.get_type_from_sku(item_sku=item_sku))
                    if is_an_accessory:
                        order_confirmed_on = create_timestamp
                        orm_order_status = 2
                    pincode_detail = get_city_state_edd_by_pincode(pincode)
                    if pincode_detail:
                        city = pincode_detail['city']
                        state = pincode_detail['state']
                        estimate_delivery = pincode_detail['edd']
                    else:
                        city = ''
                        state = ''
                        if not is_an_accessory:
                            order_confirmed_on = None
                        orm_order_status = 14
                        hold_reason_id = int(HoldReasonID.NON_SERVICABLE_PINCODE)
                        msg = f'for order_id {order_random_id} pincode {pincode} is'\
                            f' not in delivery sheet/database.Hence'\
                                f' Order moved on hold'
                        failed_cart_id_list.append(msg)
                    wf_sku = get_wf_mapped_skucode(affiliate_sku)
                    if wf_sku:
                        item_sku = wf_sku
                    else:
                        new_affiliate_sku_list.append(f'{order_random_id}: {item_sku}')
                    sku_code = Product.get_sku_code(item_sku)
                    try:
                        if pincode_detail:
                            edd_delivery = estimate_delivery.split('-')
                            if sku_code in CONST.T2_SKUS:
                                if 'edd5' in pincode_detail:
                                    edd_delivery = pincode_detail['edd5'].split('-')
                            promised_edd = promised_dispatch_timestamp + timedelta(int(edd_delivery[1]))
                    except Exception as e:
                        print("Error in updating promised_edd paytm sheet upload", e)
                    item_dimensions = Product.get_item_sku_dimensions(item_sku)
                    affiliate_obj = WfAffiliateOrders()
                    affiliate_obj.sheet_upload_id = sheet_upload_id
                    affiliate_obj.affiliate_id = PlatformId.PEPPERFRY
                    affiliate_obj.payment_type = "ECOM"
                    affiliate_obj.affiliate_order_id = affiliate_order_id
                    affiliate_obj.order_random_id = order_random_id
                    affiliate_obj.cart_id = cart_id
                    affiliate_obj.affiliate_sku = affiliate_sku
                    affiliate_obj.item_sku = item_sku
                    affiliate_obj.item_name = item_name
                    affiliate_obj.item_dimensions = item_dimensions
                    affiliate_obj.item_quantity = item_quantity
                    affiliate_obj.item_price = item_price
                    if pincode and orm_order_status == OrmStatus.NEW_ORDER.value and \
                            is_valid_phone_number(get_corrected_mobile_number(mobile_number)):
                        order_confirmed_on = create_timestamp
                        if Product.is_standard_product(item_sku):
                            orm_order_status = OrmStatus.CONFIRMED
                        else:
                            orm_order_status = OrmStatus.CONFIRMED_WITH_CUSTOMIZATION
                    affiliate_obj.orm_order_status = orm_order_status
                    affiliate_obj.hold_reason_id = hold_reason_id
                    is_standard_product = 1
                    if sku_code in CONST.MATTRESS_SKUS:
                        is_standard_product = Product.get_is_standard_product_size(item_sku)
                    affiliate_obj.is_standard_product_size = is_standard_product
                    affiliate_obj.firstname = firstname
                    affiliate_obj.lastname = lastname
                    affiliate_obj.email_address = email_address
                    affiliate_obj.mobile_number = mobile_number
                    affiliate_obj.alternate_mobile_number = alternate_mobile_number
                    affiliate_obj.address = address
                    affiliate_obj.landmark = landmark
                    affiliate_obj.pincode = pincode
                    affiliate_obj.ship_service_level = ship_service_level
                    affiliate_obj.city = city
                    affiliate_obj.state = state
                    affiliate_obj.estimate_delivery = estimate_delivery
                    affiliate_obj.promised_dispatch_timestamp = promised_dispatch_timestamp
                    affiliate_obj.promised_edd = promised_edd
                    affiliate_obj.cet_id = cet_id
                    affiliate_obj.create_timestamp = create_timestamp
                    affiliate_obj.update_timestamp = now
                    affiliate_obj.order_confirmed_on = order_confirmed_on
                    affiliate_order_list.append(affiliate_obj)
                    order_id.add(order_random_id)
                    edd_list.append([cart_id, item_sku, pincode, item_quantity])
                    successfull_count += 1
                except Exception as e:
                    print(e, "Exception")
                    failed_cart_id_list.append(order_random_id)
                    continue
            try:
                if len(affiliate_order_list) != 0:
                    list_of_object_affiliate_orders = WfAffiliateOrders.objects.bulk_create(affiliate_order_list)
                    message['success_count'] = successfull_count
                    if settings.DEBUG_CONF:
                        assign_order_cet_and_sent_notification(list(order_id), 2)
                    else:
                        assign_order_cet_and_sent_notification.apply_async(args=[list(order_id), 2])

                    # edd_affiliate_order.apply_async(args=[edd_list, 2])
                for order in affiliate_order_list:
                    try:
                        # TwoFcShippingLabel.generate_shipping_label(order.order_random_id)
                        assign_estmiated_warehouse([order.cart_id])
                        assign_shipping_label_to_order.apply_async(args=[order.order_random_id])
                    except Exception as e: # TODO-Abhinav handle log
                        logger.error(f'Exception in generating shipping label : {e}', exc_info=True )
                        pass
                    # assign_shipping_label_to_order.apply_async(args=[order.order_random_id])
                    if order.orm_order_status == OrmStatus.CONFIRMED:
                        sent_email_sms_notification.apply_async(
                            args=[StatusType.CONFIRMED, None, order.order_random_id, {}, 2])
                    elif order.orm_order_status == OrmStatus.CONFIRMED_WITH_CUSTOMIZATION:
                        sent_email_sms_notification.apply_async(
                            args=[StatusType.CONFIRMED, None, order.order_random_id, {}, 2])

                if len(new_affiliate_sku_list) != 0:
                    mail_title = 'Pepperfry New SKU Code'
                    mail_body = f'New_Sku-{new_affiliate_sku_list}'
                    email_to = ['tech-team@wakefit.co']
                    send_mail_only.apply_async(args=[mail_title, mail_body, email_to, [], []])
                WfAffiliateSheetUploads.objects.filter(
                    id=sheet_upload_id).update(
                        total_orders=total_orders,
                        new_orders=successfull_count,
                        failed_orders=tuple(failed_cart_id_list) if failed_cart_id_list else ''
                    )
                s3_path = f'excels-copy/affiliate-excels/{file_name}'
                upload_file_s3(file_path + file_name, s3_path, True)

            except Exception as e:
                print(e, "Error in bulk create pepperfry orders")
                message['success_count'] = 0
                message['failed_cart_ids'] = order_id
                mail_title = 'Error Pepperfry Excel Upload'
                mail_body = f'Error in bulk create pepperfry orders'
                exec_str = str(traceback.format_exc())
                send_error_mail.apply_async(args=[mail_title, mail_body, str(e), exec_str])
            return Response(
                {"message": message},
                status=status.HTTP_200_OK)
        elif affiliate_id == 4:
            try:
                aff_sheet = WfAffiliateSheetUploads.objects.create(
                    affiliate_id=4,
                    sheet_name=file_name_format,
                    upload_by=upload_by,
                    upload_by_id=upload_by_id,
                    created_timestamp=now,
                    is_active=1
                )
            except Exception as e:
                print(e, "Exception")
                msg = 'Error in creation of sheet upload row'
                return Response(
                    {"error": msg},
                    status=status.HTTP_400_BAD_REQUEST)
            sheet_upload_id = aff_sheet.id
            check_dict = {}
            check_status = 0
            check_list_duplicate_orders = []
            for row in range(2, m_row+1):
                try:
                    get_cart_id =\
                        sheet_obj.cell(
                            row = row, column=column_index_from_string('A')).value
                    if get_cart_id is None:
                        continue
                    else:
                        check_status += 1
                        check_dict[get_cart_id] = check_dict.get(get_cart_id, 0) + 1
                        if check_dict[get_cart_id] > 1:
                            check_list_duplicate_orders.append(get_cart_id)
                except Exception as e:
                    print(check_list_duplicate_orders, check_status, check_dict)
                    print("Exception in Paytm sheet", e)
            if not(len(check_dict) == check_status):
                msg = 'Duplicate orders found'
                return Response(
                    {"error": msg, "duplicate_order": check_list_duplicate_orders},
                    status=status.HTTP_400_BAD_REQUEST)

            for row in range(2, m_row+1):
                hold_reason_id = 0
                try:
                    affiliate_order_id =\
                        sheet_obj.cell(
                            row = row, column=column_index_from_string('B')).value
                    if affiliate_order_id is None:
                        continue
                    total_orders += 1
                    affiliate_order_id = int(affiliate_order_id)
                    order_random_id =\
                        sheet_obj.cell(
                            row = row, column=column_index_from_string('B')).value
                    order_random_id = int(order_random_id)
                    cart_id1 =\
                        sheet_obj.cell(
                            row = row, column=column_index_from_string('A')).value
                    cart_id = int(cart_id1)
                    order_exist =\
                        check_existing_affiliate_order(
                            cart_id, affiliate_id=4)
                    if order_exist:
                        existing_cart_id_list.append(cart_id)
                        continue
                    affiliate_sku =\
                        sheet_obj.cell(
                            row = row, column=column_index_from_string('E')).value
                    item_sku =\
                        sheet_obj.cell(
                            row = row, column=column_index_from_string('E')).value.strip()
                    item_name =\
                        sheet_obj.cell(
                            row = row, column=column_index_from_string('F')).value
                    item_dimensions = ''
                    item_quantity =\
                        sheet_obj.cell(
                            row = row, column=column_index_from_string('G')).value
                    item_price =\
                        sheet_obj.cell(
                            row = row, column=column_index_from_string('N')).value
                    orm_order_status = 1
                    firstname =\
                        sheet_obj.cell(
                            row = row, column=column_index_from_string('V')).value
                    lastname1 =\
                        sheet_obj.cell(
                            row = row, column=column_index_from_string('W')).value
                    lastname = lastname1 if lastname1 else ''
                    email_address1 =\
                        sheet_obj.cell(
                            row = row, column=column_index_from_string('U')).value
                    email_address = email_address1 if email_address1 else ''
                    mobile_number1 =\
                        sheet_obj.cell(
                            row = row, column=column_index_from_string('AB')).value
                    mobile_number = mobile_number1 if mobile_number1 else ''
                    mobile_number =\
                        str(mobile_number).split('.')[0].replace(' ','')
                    alternate_mobile_number = ''
                    address =\
                        sheet_obj.cell(
                            row = row, column=column_index_from_string('Z')).value
                    landmark = ''
                    pincode =\
                        sheet_obj.cell(
                            row = row, column=column_index_from_string('Y')).value
                    pincode = int(pincode)
                    ship_service_level = None
                    city =\
                        sheet_obj.cell(
                            row = row, column=column_index_from_string('AA')).value
                    state =\
                        sheet_obj.cell(
                            row = row, column=column_index_from_string('X')).value
                    estimate_delivery = ''
                    create_timestamp =\
                        sheet_obj.cell(
                            row = row, column=column_index_from_string('R')).value
                    if type(create_timestamp) != datetime:
                        create_timestamp = create_timestamp.split('.')[0]
                        create_timestamp = datetime.strptime(create_timestamp, '%Y-%m-%dT%H:%M:%S')
                        create_timestamp = timezone.make_aware(create_timestamp)
                    else:
                        create_timestamp = timezone.make_aware(create_timestamp)
                    promised_dispatch_timestamp =\
                        sheet_obj.cell(
                            row = row, column=column_index_from_string('AO')).value
                    if type(promised_dispatch_timestamp) != datetime:
                        promised_dispatch_timestamp = promised_dispatch_timestamp.split('.')[0]
                        promised_dispatch_timestamp = datetime.strptime(promised_dispatch_timestamp, '%Y-%m-%dT%H:%M:%S')
                        promised_dispatch_timestamp = timezone.make_aware(promised_dispatch_timestamp)
                    else:
                        promised_dispatch_timestamp = timezone.make_aware(promised_dispatch_timestamp)
                    order_confirmed_on = None
                    is_an_accessory =\
                        Product.check_product_an_accessory(Product.get_type_from_sku(item_sku=item_sku))
                    if is_an_accessory:
                        order_confirmed_on = create_timestamp
                        orm_order_status = 2
                    pincode_detail =\
                        get_city_state_edd_by_pincode(pincode)
                    if pincode_detail:
                        city = pincode_detail['city']
                        state = pincode_detail['state']
                        estimate_delivery = pincode_detail['edd']
                    else:
                        if not is_an_accessory:
                            order_confirmed_on = None
                        orm_order_status = 14
                        hold_reason_id = int(HoldReasonID.NON_SERVICABLE_PINCODE)
                        msg = f'for order_id {order_random_id} pincode {pincode} is'\
                            f' not in delivery sheet/database.Hence'\
                                f' Order moved on hold'
                        failed_cart_id_list.append(msg)
                    if item_dimensions == '':
                        id_check, id_dimension = Product.get_item_dimension_from_sku(item_sku)
                        item_dimensions = id_dimension if id_check else ''
                    check_result, check_msg = Product.is_valid_sku(item_sku, item_dimensions)
                    if check_result:
                        item_sku = item_sku
                    else:
                        new_affiliate_sku_list.append(f'{order_random_id}: {item_sku}')
                    sku_code = Product.get_sku_code(item_sku)
                    try:
                        if pincode_detail:
                            edd_delivery = estimate_delivery.split('-')
                            if sku_code in CONST.T2_SKUS:
                                if 'edd5' in pincode_detail:
                                    edd_delivery = pincode_detail['edd5'].split('-')
                            promised_edd = promised_dispatch_timestamp + timedelta(int(edd_delivery[1]))
                    except Exception as e:
                        print("Error in updating promised_edd paytm sheet upload", e)
                    affiliate_obj = WfAffiliateOrders()
                    affiliate_obj.sheet_upload_id = sheet_upload_id
                    affiliate_obj.affiliate_id = 4
                    affiliate_obj.payment_type = "ECOM"
                    affiliate_obj.affiliate_order_id = affiliate_order_id
                    affiliate_obj.order_random_id = order_random_id
                    affiliate_obj.cart_id = cart_id
                    affiliate_obj.affiliate_sku = affiliate_sku
                    affiliate_obj.item_sku = item_sku
                    affiliate_obj.item_name = item_name
                    affiliate_obj.item_dimensions = item_dimensions
                    affiliate_obj.item_quantity = item_quantity
                    affiliate_obj.item_price = item_price
                    if pincode and orm_order_status == OrmStatus.NEW_ORDER.value and \
                            is_valid_phone_number(get_corrected_mobile_number(mobile_number)):
                        order_confirmed_on = create_timestamp
                        if Product.is_standard_product(item_sku):
                            orm_order_status = OrmStatus.CONFIRMED
                        else:
                            orm_order_status = OrmStatus.CONFIRMED_WITH_CUSTOMIZATION
                    is_standard_product = 1
                    if sku_code in CONST.MATTRESS_SKUS:
                        is_standard_product = Product.get_is_standard_product_size(item_sku)
                    affiliate_obj.is_standard_product_size = is_standard_product
                    affiliate_obj.orm_order_status = orm_order_status
                    affiliate_obj.hold_reason_id = hold_reason_id
                    affiliate_obj.firstname = firstname
                    affiliate_obj.lastname = lastname
                    affiliate_obj.email_address = email_address
                    affiliate_obj.mobile_number = mobile_number
                    affiliate_obj.alternate_mobile_number =\
                        alternate_mobile_number
                    affiliate_obj.address = address
                    # gst_extract_result = gst_extract(address)
                    # if gst_extract_result:
                    #     affiliate_obj.gst_number = gst_extract_result
                    affiliate_obj.landmark = landmark
                    affiliate_obj.pincode = pincode
                    affiliate_obj.ship_service_level = ship_service_level
                    affiliate_obj.city = city
                    affiliate_obj.state = state
                    affiliate_obj.estimate_delivery = estimate_delivery
                    affiliate_obj.cet_id = cet_id
                    affiliate_obj.create_timestamp = create_timestamp
                    affiliate_obj.update_timestamp = now
                    affiliate_obj.order_confirmed_on = order_confirmed_on
                    affiliate_obj.promised_dispatch_timestamp = promised_dispatch_timestamp
                    affiliate_obj.promised_edd = promised_edd
                    affiliate_order_list.append(affiliate_obj)
                    order_id.add(order_random_id)
                    edd_list.append([cart_id, item_sku, pincode, item_quantity])
                    successfull_count += 1
                except Exception as e:
                    print(e, "Exception")
                    failed_cart_id_list.append(order_random_id)
                    continue
            try:
                if len(affiliate_order_list) != 0:
                    list_of_object_affiliate_orders = WfAffiliateOrders.objects.bulk_create(affiliate_order_list)
                    message['success_count'] = successfull_count
                    if settings.DEBUG_CONF:
                        assign_order_cet_and_sent_notification(list(order_id), 4)
                    else:
                        assign_order_cet_and_sent_notification.apply_async(args=[list(order_id), 4])
                    for order in affiliate_order_list:
                        try:
                            # TwoFcShippingLabel.generate_shipping_label(order.order_random_id)
                            assign_estmiated_warehouse([order.cart_id])
                            assign_shipping_label_to_order.apply_async(args=[order.order_random_id])
                        except Exception as e: # TODO-Abhinav handle log
                            logger.error(f'Exception in generating shipping label : {e}', exc_info=True )
                            pass
                        # assign_shipping_label_to_order.apply_async(args=[order.order_random_id])
                        if order.orm_order_status == OrmStatus.CONFIRMED:
                            sent_email_sms_notification.apply_async(
                                args=[StatusType.CONFIRMED, None, order.order_random_id, {}, 4])
                        elif order.orm_order_status == OrmStatus.CONFIRMED_WITH_CUSTOMIZATION:
                            sent_email_sms_notification.apply_async(
                                args=[StatusType.CONFIRMED, None, order.order_random_id, {}, 4])

                    # edd_affiliate_order.apply_async(args=[edd_list, 4])
                if len(new_affiliate_sku_list) != 0:
                    mail_title = 'Paytm New SKU Code'
                    mail_body = f'New_Sku-{new_affiliate_sku_list}'
                    email_to = ['tech-team@wakefit.co']
                    send_mail_only.apply_async(args=[mail_title, mail_body, email_to, [], []])
                WfAffiliateSheetUploads.objects.filter(
                    id=sheet_upload_id).update(
                        total_orders=total_orders,
                        new_orders=successfull_count,
                        failed_orders=tuple(failed_cart_id_list) if failed_cart_id_list else ''
                    )
                s3_path = f'excels-copy/affiliate-excels/{file_name}'
                upload_file_s3(file_path + file_name, s3_path, True)

            except Exception as e:
                print(e, "Error in bulk create paytm orders")
                message['success_count'] = 0
                message['failed_cart_ids'] = order_id
                mail_title = 'Error Paytm Excel Upload'
                mail_body = f'Error in bulk create paytm orders'
                exec_str = str(traceback.format_exc())
                send_error_mail.apply_async(args=[mail_title, mail_body, str(e), exec_str])
            return Response(
                {"message": message},
                status=status.HTTP_200_OK)

        elif affiliate_id == 1001:
            try:
                aff_sheet = WfAffiliateSheetUploads.objects.create(
                    affiliate_id=1001,
                    sheet_name=file_name_format,
                    upload_by=upload_by,
                    upload_by_id=upload_by_id,
                    created_timestamp=now,
                    is_active=1
                )
            except Exception as e:
                print(e, "Exception in creation of sheet upload row")
                msg = 'Error in creation of sheet upload row'
                return Response(
                    {"error": msg},
                    status=status.HTTP_400_BAD_REQUEST)

            fba_forward_data = fin_fba[fin_fba['Transaction Type'] != 'Refund'] \
                [['Invoice Number', 'Invoice Date', 'Transaction Type',
                  'Order Id', 'Shipment Date', 'Order Date', 'Quantity', 'Item Description', 'Hsn/sac',
                  'Sku', 'Bill From State', 'Ship To City', 'Ship To State',
                  'Ship To Postal Code', 'Invoice Amount', 'Tax Exclusive Gross',
                  'Total Tax Amount', 'Cgst Rate', 'Sgst Rate', 'Utgst Rate', 'Igst Rate',
                  'Principal Amount', 'Principal Amount Basis', 'Cgst Tax', 'Sgst Tax', 'Igst Tax',
                  'Utgst Tax', 'Shipping Amount', 'Shipping Amount Basis',
                  'Shipping Cgst Tax', 'Shipping Sgst Tax', 'Shipping Utgst Tax',
                  'Shipping Igst Tax', 'Item Promo Discount Basis', 'Item Promo Discount Tax',
                  'Shipping Promo Discount', 'Shipping Promo Discount Basis',
                  'Shipping Promo Discount Tax', 'Fulfillment Channel']].copy()
            fba_forward_data_list = []
            for index, row in fba_forward_data.iterrows():
                data_obj = WfFbaForwardData()
                if row['Invoice Number'] is not '':
                    data_obj.invoice_number = row['Invoice Number']
                if check_existing_invoice_no_in_amazon_fba(data_obj.invoice_number):
                    existing_invoice_no_list.append(data_obj.invoice_number)
                    continue
                if row['Invoice Date'] is not '':
                    data_obj.invoice_date = row['Invoice Date'].replace(tzinfo=pytz.timezone('Asia/Calcutta'))
                if row['Transaction Type'] is not '':
                    data_obj.transaction_type = row['Transaction Type']
                if row['Order Id'] is not '':
                    data_obj.order_id = row['Order Id']
                if row['Shipment Date'] is not '':
                    data_obj.shipment_date = row['Shipment Date'].replace(tzinfo=pytz.timezone('Asia/Calcutta'))
                if row['Order Date'] is not '':
                    data_obj.order_date = row['Order Date'].replace(tzinfo=pytz.timezone('Asia/Calcutta'))
                if row['Quantity'] is not '':
                    data_obj.quantity = row['Quantity']
                if row['Item Description'] is not '':
                    data_obj.item_description = row['Item Description']
                if row['Hsn/sac'] is not '':
                    data_obj.hsn_sac = row['Hsn/sac']
                if row['Sku'] is not '':
                    wf_sku = get_wf_mapped_skucode(row['Sku'])
                    data_obj.sku = wf_sku if wf_sku else row['Sku']
                if row['Bill From State'] is not '':
                    data_obj.bill_from_state = row['Bill From State']
                if row['Ship To City'] is not '':
                    data_obj.ship_to_city = row['Ship To City']
                if row['Ship To State'] is not '':
                    data_obj.ship_to_state = row['Ship To State']
                if row['Ship To Postal Code'] is not '':
                    data_obj.ship_to_postal_code = row['Ship To Postal Code']
                if row['Invoice Amount'] is not '':
                    data_obj.invoice_amount = row['Invoice Amount']
                if row['Tax Exclusive Gross'] is not '':
                    data_obj.tax_exclusive_gross = row['Tax Exclusive Gross']
                if row['Total Tax Amount'] is not '':
                    data_obj.total_tax_amount = row['Total Tax Amount']
                if row['Cgst Rate'] is not '':
                    data_obj.cgst_rate = row['Cgst Rate']
                if row['Sgst Rate'] is not '':
                    data_obj.sgst_rate = row['Sgst Rate']
                if row['Utgst Rate'] is not '':
                    data_obj.utgst_rate = row['Utgst Rate']
                if row['Igst Rate'] is not '':
                    data_obj.igst_rate = row['Igst Rate']
                if row['Principal Amount'] is not '':
                    data_obj.principal_amount = row['Principal Amount']
                if row['Principal Amount Basis'] is not '':
                    data_obj.principal_amount_basis = row['Principal Amount Basis']
                if row['Cgst Tax'] is not '':
                    data_obj.cgst_tax = row['Cgst Tax']
                if row['Sgst Tax'] is not '':
                    data_obj.sgst_tax = row['Sgst Tax']
                if row['Igst Tax'] is not '':
                    data_obj.igst_tax = row['Igst Tax']
                if row['Utgst Tax'] is not '':
                    data_obj.utgst_tax = row['Utgst Tax']
                if row['Shipping Amount'] is not '':
                    data_obj.shipping_amount = row['Shipping Amount']
                if row['Shipping Amount Basis'] is not '':
                    data_obj.shipping_amount_basis = row['Shipping Amount Basis']
                if row['Shipping Cgst Tax'] is not '':
                    data_obj.shipping_cgst_tax = row['Shipping Cgst Tax']
                if row['Shipping Sgst Tax'] is not '':
                    data_obj.shipping_sgst_tax = row['Shipping Sgst Tax']
                if row['Shipping Utgst Tax'] is not '':
                    data_obj.shipping_utgst_tax = row['Shipping Utgst Tax']
                if row['Shipping Igst Tax'] is not '':
                    data_obj.shipping_igst_tax = row['Shipping Igst Tax']
                if row['Item Promo Discount Basis'] is not '':
                    data_obj.item_promo_discount_basis = row['Item Promo Discount Basis']
                if row['Item Promo Discount Tax'] is not '':
                    data_obj.item_promo_tax = row['Item Promo Discount Tax']
                if row['Shipping Promo Discount'] is not '':
                    data_obj.shipping_promo_discount = row['Shipping Promo Discount']
                if row['Shipping Promo Discount Basis'] is not '':
                    data_obj.shipping_promo_discount_basis = row['Shipping Promo Discount Basis']
                if row['Shipping Promo Discount Tax'] is not '':
                    data_obj.shipping_promo_tax = row['Shipping Promo Discount Tax']
                if row['Fulfillment Channel'] is not '':
                    data_obj.fulfillment_channel = row['Fulfillment Channel']
                fba_forward_data_list.append(data_obj)
                successful_count_for_forward_data+=1

            fba_return_data = fin_fba[fin_fba['Transaction Type'] == 'Refund'] \
                [['Invoice Number', 'Invoice Date', 'Transaction Type',
                  'Order Id', 'Shipment Date', 'Order Date', 'Quantity', 'Item Description', 'Hsn/sac',
                  'Sku', 'Bill From State', 'Ship To City', 'Ship To State',
                  'Ship To Postal Code', 'Invoice Amount', 'Tax Exclusive Gross',
                  'Total Tax Amount', 'Cgst Rate', 'Sgst Rate', 'Utgst Rate', 'Igst Rate',
                  'Principal Amount', 'Principal Amount Basis', 'Cgst Tax', 'Sgst Tax', 'Igst Tax',
                  'Utgst Tax', 'Shipping Amount', 'Shipping Amount Basis',
                  'Shipping Cgst Tax', 'Shipping Sgst Tax', 'Shipping Utgst Tax',
                  'Shipping Igst Tax', 'Item Promo Discount Basis', 'Item Promo Discount Tax',
                  'Shipping Promo Discount', 'Shipping Promo Discount Basis',
                  'Shipping Promo Discount Tax', 'Fulfillment Channel', 'Credit Note No', 'Credit Note Date']].copy()
            fba_return_data_list = []
            for index, row in fba_return_data.iterrows():
                data_obj = WfFbaReturnData()
                if row['Invoice Number'] is not '':
                    data_obj.invoice_number = row['Invoice Number']
                if check_existing_invoice_no_in_amazon_fba(data_obj.invoice_number):
                    existing_invoice_no_list.append(data_obj.invoice_number)
                    continue
                if row['Invoice Date'] is not '':
                    data_obj.invoice_date = row['Invoice Date'].replace(tzinfo=pytz.timezone('Asia/Calcutta'))
                if row['Transaction Type'] is not '':
                    data_obj.transaction_type = row['Transaction Type']
                if row['Order Id'] is not '':
                    data_obj.order_id = row['Order Id']
                if row['Shipment Date'] is not '':
                    data_obj.shipment_date = row['Shipment Date'].replace(tzinfo=pytz.timezone('Asia/Calcutta'))
                if row['Order Date'] is not '':
                    data_obj.order_date = row['Order Date'].replace(tzinfo=pytz.timezone('Asia/Calcutta'))
                if row['Quantity'] is not '':
                    data_obj.quantity = row['Quantity']
                if row['Item Description'] is not '':
                    data_obj.item_description = row['Item Description']
                if row['Hsn/sac'] is not '':
                    data_obj.hsn_sac = row['Hsn/sac']
                if row['Sku'] is not '':
                    wf_sku = get_wf_mapped_skucode(row['Sku'])
                    data_obj.sku = wf_sku if wf_sku else row['Sku']
                if row['Bill From State'] is not '':
                    data_obj.bill_from_state = row['Bill From State']
                if row['Ship To City'] is not '':
                    data_obj.ship_to_city = row['Ship To City']
                if row['Ship To State'] is not '':
                    data_obj.ship_to_state = row['Ship To State']
                if row['Ship To Postal Code'] is not '':
                    data_obj.ship_to_postal_code = row['Ship To Postal Code']
                if row['Invoice Amount'] is not '':
                    data_obj.invoice_amount = row['Invoice Amount']
                if row['Tax Exclusive Gross'] is not '':
                    data_obj.tax_exclusive_gross = row['Tax Exclusive Gross']
                if row['Total Tax Amount'] is not '':
                    data_obj.total_tax_amount = row['Total Tax Amount']
                if row['Cgst Rate'] is not '':
                    data_obj.cgst_rate = row['Cgst Rate']
                if row['Sgst Rate'] is not '':
                    data_obj.sgst_rate = row['Sgst Rate']
                if row['Utgst Rate'] is not '':
                    data_obj.utgst_rate = row['Utgst Rate']
                if row['Igst Rate'] is not '':
                    data_obj.igst_rate = row['Igst Rate']
                if row['Principal Amount'] is not '':
                    data_obj.principal_amount = row['Principal Amount']
                if row['Principal Amount Basis'] is not '':
                    data_obj.principal_amount_basis = row['Principal Amount Basis']
                if row['Cgst Tax'] is not '':
                    data_obj.cgst_tax = row['Cgst Tax']
                if row['Sgst Tax'] is not '':
                    data_obj.sgst_tax = row['Sgst Tax']
                if row['Igst Tax'] is not '':
                    data_obj.igst_tax = row['Igst Tax']
                if row['Utgst Tax'] is not '':
                    data_obj.utgst_tax = row['Utgst Tax']
                if row['Shipping Amount'] is not '':
                    data_obj.shipping_amount = row['Shipping Amount']
                if row['Shipping Amount Basis'] is not '':
                    data_obj.shipping_amount_basis = row['Shipping Amount Basis']
                if row['Shipping Cgst Tax'] is not '':
                    data_obj.shipping_cgst_tax = row['Shipping Cgst Tax']
                if row['Shipping Sgst Tax'] is not '':
                    data_obj.shipping_sgst_tax = row['Shipping Sgst Tax']
                if row['Shipping Utgst Tax'] is not '':
                    data_obj.shipping_utgst_tax = row['Shipping Utgst Tax']
                if row['Shipping Igst Tax'] is not '':
                    data_obj.shipping_igst_tax = row['Shipping Igst Tax']
                if row['Item Promo Discount Basis'] is not '':
                    data_obj.item_promo_discount_basis = row['Item Promo Discount Basis']
                if row['Item Promo Discount Tax'] is not '':
                    data_obj.item_promo_tax = row['Item Promo Discount Tax']
                if row['Shipping Promo Discount'] is not '':
                    data_obj.shipping_promo_discount = row['Shipping Promo Discount']
                if row['Shipping Promo Discount Basis'] is not '':
                    data_obj.shipping_promo_discount_basis = row['Shipping Promo Discount Basis']
                if row['Shipping Promo Discount Tax'] is not '':
                    data_obj.shipping_promo_tax = row['Shipping Promo Discount Tax']
                if row['Fulfillment Channel'] is not '':
                    data_obj.fulfillment_channel = row['Fulfillment Channel']
                if row['Credit Note No'] is not '':
                    data_obj.credit_note_no = row['Credit Note No']
                if row['Credit Note Date'] is not '':
                    data_obj.credit_note_date = row['Credit Note Date'].replace(tzinfo=pytz.timezone('Asia/Calcutta'))
                fba_return_data_list.append(data_obj)
                successful_count_for_return_data+=1

            try:
                WfFbaForwardData.objects.bulk_create(fba_forward_data_list)
                WfFbaReturnData.objects.bulk_create(fba_return_data_list)
                s3_path = f'excels-copy/affiliate-excels/{file_name}'
                upload_file_s3(file_path + file_name, s3_path, True)

                message["success_count_for_forward_data"] = successful_count_for_forward_data
                message["success_count_for_return_data"] = successful_count_for_return_data

                print(f'success_count_for_forward_data = {successful_count_for_forward_data}\
                success_count_for_return_data = {successful_count_for_return_data}, message = {message}')

            except Exception as e:
                print(e, "Error in bulk create amazon fba orders")
                message["success_count_for_forward_data"] = 0
                message["success_count_for_return_data"] = 0
                mail_title = '[Error Amazon FBA Excel Upload]'
                mail_body = f'Error is bulk create amazon fba orders'
                exec_str = str(traceback.format_exc())
                send_error_mail.apply_async(args=[mail_title, mail_body, str(e), exec_str])
            return Response(
                {"message": message},
                status=status.HTTP_200_OK)

        else:
            msg = 'Affiliate id is invalid'
            return Response(
                {"error": msg},
                status=status.HTTP_400_BAD_REQUEST)