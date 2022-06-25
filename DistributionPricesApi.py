class DistributorPricingAPI(APIView):
    """This API fetches distributor pricing data from the excel sheet uploaded from CRM"""
    authentication_classes = (JWTTokenAuthentication,)
    permission_classes = [CustomUserAccessBasedPermission]

    permission_map = {
        'POST': {AuthRole.DISTRIBUTION_MANAGER: ''},
    }

    def post(self, request):
        logger.info(f'[DistributorPricingAPI] Data: {request.data}')

        try:
            attachment_data = request.data['attachments']
        except Exception as e:
            return Response({"message": f"Invalid data given. {e}"}, status=status.HTTP_404_NOT_FOUND)

        try:
            attachment_bytes_data_decodes = base64.b64decode(attachment_data)
            attachment_to_read = io.BytesIO()
            attachment_to_read.write(attachment_bytes_data_decodes)
            attachment_to_read.seek(0)
            df_dict = pd.read_excel(attachment_to_read, sheet_name=None)
        except Exception as e:  # pylint: disable=broad-except
            error_msg = 'Required Attachment not given!'
            logger.error(f'[DistributorPricingAPI] Error: {error_msg}, Exception: {e}', exc_info=True)
            raise MessageBadRequest('Unsupported format, or corrupt file') from e

        # If excel sheet is empty
        if len(df_dict) == 0:
            raise MessageBadRequest('Excel file has no data')

        data = next(iter(df_dict.values())).values.tolist()
        logger.info(data)

        # Check for 0 data rows in sheet
        if not data:
            raise MessageBadRequest("No data row in sheet")

        # Check for missing columns
        if data and len(data[0]) != 4:
            raise MessageBadRequest('Some columns are missing in the uploaded sheet.')

        error_list = []
        pricing_list = []
        pricing_log_list = []
        id_list = set()
        validator = Validator(DISTRIBUTION_PRICING_SCHEMA)

        for item_sku, mrp, price, active in data:
            try:
                data_dict = {'item_sku': item_sku, 'mrp': mrp, 'price': price, 'active': int(active)}
                if not validator(data_dict):
                    error_list.append(f'{item_sku}:{mrp}:{price}:{active}:{validator.errors}')
                    continue
                product_data = ProductPricing.objects.filter(
                    item_sku=item_sku, active=True).values('id', 'dimension').first()
                if not product_data:
                    raise MessageBadRequest(f'{item_sku} does not exist in wf_products_pricing table')
                else:
                    if product_data["id"] in id_list:
                        continue
                    id_list.add(product_data["id"])
                pricing_dict = {
                    "product_pricing_id": product_data["id"],
                    "mrp": mrp,
                    "price": price,
                    "active": active
                }
                pricing_list.append(pricing_dict)

                old_price = DistributorProductPricing.objects.filter(
                    product_pricing=product_data["id"], active=True).values_list('price', flat=True).first()
                pricing_log_obj = DistributorPricingLog()
                pricing_log_obj.item_sku = item_sku
                pricing_log_obj.item_dimensions = product_data["dimension"]
                pricing_log_obj.old_price = old_price if old_price else 0
                pricing_log_obj.new_price = price
                pricing_log_obj.uploaded_by_id = request.user['login_id']
                pricing_log_obj.uploaded_by_auth_role_id = request.user['auth_role_id']
                pricing_log_list.append(pricing_log_obj)
            except Exception as e:
                error_list.append(f'{item_sku}:{mrp}:{price}:{active}:{str(e)}')
        if error_list:
            raise MessageBadRequest('\n'.join(error_list))

        try:
            with transaction.atomic():
                if pricing_list:
                    for d in pricing_list:
                        pp_id = d['product_pricing_id']
                        del d['product_pricing_id']
                        DistributorProductPricing.objects.update_or_create(
                            product_pricing_id=pp_id, defaults=d
                        )

                if len(pricing_log_list) != 0:
                    DistributorPricingLog.objects.bulk_create(pricing_log_list, batch_size=100)
        except Exception as e:
            return Response({"message": e}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"status": SUCCESS, "message": "Uploaded successfully!"})