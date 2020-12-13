

def get_client_ip(get_response):
    def process_request(request):
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            try:
                ip = x_forwarded_for.split(",")[0].strip()
            except IndexError:
                ip = x_forwarded_for.strip()
        else:
            ip = request.META.get("REMOTE_ADDR")
        request.META["CLIENT_IP"] = ip
        return get_response(request)

    return process_request
