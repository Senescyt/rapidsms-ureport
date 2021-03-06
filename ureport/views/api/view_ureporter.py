from django.http import HttpResponse
from ureport.views.api.base import UReporterApiView


class ViewUReporter(UReporterApiView):
    def get(self, request, *args, **kwargs):
        status_code = 200
        response_data = {"success": True}
        contact = self.get_contact()
        error_message = "Ureporter not found"
        if not contact["registered"]:
            status_code = 404
            response_data["success"] = False
            response_data["reason"] = error_message
        else:
            response_data["user"] = contact
        return self.create_json_response(response_data, status_code)

    def post(self, request, *args, **kwargs):
        return HttpResponse("Method Not Allowed", status=405)

    def get_contact(self):
        contact_data = {"language": "", "registered": False}
        if (self.contact_exists(self.connection)):
            contact_data["registered"] = True
            contact_data["language"] = self.connection.contact.language

        return contact_data

