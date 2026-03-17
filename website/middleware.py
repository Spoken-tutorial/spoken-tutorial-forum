from django.conf import settings
from django.shortcuts import render
from forums.settings import RECAPTCHA_SITE_KEY_v3

class FilterCaptchaGateMiddleware(object):
    """
    Protects expensive /filter/ GET pages.

    Rules:
    - page 1 with default sorting is allowed anonymously
    - page > 1 requires prior verification
    - any sorting (o=...) requires prior verification
    - invalid page values are challenged early
    """
    def __init__(self, get_response=None):
        self.get_response = get_response

    def __call__(self, request):
        
        path = request.path
        
        # Only apply to filter endpoints
        if path.startswith('/filter/'):

            # return if already verified 
            if request.session.get('filter_verified', False):
                return self.get_response(request) 
            
            page = request.GET.get('page', '1')
            ordering = request.GET.get('o', None)

            # Validate page early
            if page is None or page == '':
                page = 1
            page_num = int(page)
            
            # Challenge if:
            # - deeper page, OR
            # - any sorting is used
            needs_verification = (page_num > 1) or bool(ordering)
            if needs_verification:
                    context = {
                        'next_url': request.get_full_path(),
                        'site_key': RECAPTCHA_SITE_KEY_v3
                    }
                    return render(request, 'website/templates/filter_verify.html',context)
        
        return self.get_response(request)
