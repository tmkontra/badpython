

def set_client_ip(get_response):
    def process_request(request):
        ip = request.META.get('HTTP_CF_CONNECTING_IP')
        if ip is None:
            ip = request.META.get("HTTP_X_REAL_IP")
        if ip is None:
            ip = request.META.get('REMOTE_ADDR')
        if ip is None:
            x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
            if x_forwarded_for:
                try:
                    ip = x_forwarded_for.split(",")[0].strip()
                except IndexError:
                    ip = x_forwarded_for.strip()
        request.META["CLIENT_IP"] = ip
        return get_response(request)

    return process_request
