
# import re

# import frappe
# from frappe import _
# from frappe.utils import cint

# from frappe.utils.password import update_password



# @frappe.whitelist()
# def create_user_for_employee(employee):
#     # Only authorized HR staff can create employee accounts.
#     # if not (
#     #     frappe.has_role("System Manager")
#     #     or frappe.has_role("HR Manager")
#     # ):

#     roles = frappe.get_roles(frappe.session.user)

#     if not ("System Manager" in roles or "HR Manager" in roles):
#         frappe.throw(
#             _("Only System Manager or HR Manager can create accounts."),
#             frappe.PermissionError,
#         )

#     emp = frappe.get_doc("Employee", employee)
#     emp.check_permission("write")

#     if not emp.cell_number:
#         frappe.throw(_("Please enter the employee's mobile number first."))

#     if emp.user_id:
#         frappe.throw(_("This Employee already has a linked User."))

#     # Normalize the number consistently with your company's phone policy.
#     mobile = re.sub(r"[\s\-()]", "", emp.cell_number)

#     if not re.fullmatch(r"\+?[0-9]{10,15}", mobile):
#         frappe.throw(
#             _("Enter a valid mobile number, including country code if needed.")
#         )

#     # The mobile number must be unique among User accounts.
#     if frappe.db.exists("User", {"mobile_no": mobile}):
#         frappe.throw(_("This mobile number is already assigned to a User."))

#     # Internal identifier only; this is not a real mailbox.
#     safe_id = re.sub(r"[^a-zA-Z0-9-]", "-", emp.name.lower())
#     user_id = f"{safe_id}@users.invalid"

#     if frappe.db.exists("User", user_id):
#         frappe.throw(_("An account already exists with this internal ID."))

#     user = frappe.new_doc("User")
#     user.update({
#         "email": user_id,
#         "first_name": emp.employee_name or emp.name,
#         "mobile_no": mobile,
#         "phone": mobile,
#         "user_type": "System User",
#         "enabled": 1,
#         "send_welcome_email": 0,
#     })

#     # Link first so ERPNext's employee-role validation can find the mapping.
#     emp.db_set("user_id", user_id, update_modified=False)

#     try:
#         user.append("roles", {"role": "Employee Self Service"})
#         user.insert(ignore_permissions=True)
#     except Exception:
#         # The request should roll back if account creation fails.
#         raise

#     return {
#         "user_id": user.name,
#         "employee": emp.name,
#         "mobile_no": mobile,
#         "message": "User account created and linked to Employee.",
#     }



import re

import frappe
from frappe import _
from frappe.utils.password import update_password


@frappe.whitelist()
def create_user_for_employee(employee):
    # Only HR Manager or System Manager can manage employee accounts.
    roles = frappe.get_roles(frappe.session.user)
    if not ({"System Manager", "HR Manager"} & set(roles)):
        frappe.throw(
            _("Only System Manager or HR Manager can manage accounts."),
            frappe.PermissionError,
        )

    emp = frappe.get_doc("Employee", employee)
    emp.check_permission("write")

    if emp.status != "Active":
        frappe.throw(_("Only active Employees can have accounts managed."))

    if not emp.cell_number:
        frappe.throw(_("Please enter the employee's mobile number."))

    mobile = re.sub(r"[\s\-()]", "", emp.cell_number)
    if not re.fullmatch(r"\+?[0-9]{10,15}", mobile):
        frappe.throw(_("Enter a valid mobile number."))

    password = emp.get_password("custom_password")
    role_profile = emp.custom_role_profile

    if not password and not emp.user_id:
        frappe.throw(_("Enter a password in Custom Password first."))

    if not role_profile:
        frappe.throw(_("Select a Role Profile first."))

    if not frappe.db.exists("Role Profile", role_profile):
        frappe.throw(_("The selected Role Profile does not exist."))

    # Reuse the linked account when it already exists.
    user_id = emp.user_id

    if user_id:
        if not frappe.db.exists("User", user_id):
            frappe.throw(
                _("The linked User {0} does not exist.").format(user_id)
            )
        user = frappe.get_doc("User", user_id)
        if not user.enabled:
            frappe.throw(_("This User account is disabled."))
    else:
        # Generate an internal identifier, not an employee email address.
        safe_id = re.sub(r"[^a-zA-Z0-9-]", "-", emp.name.lower())
        user_id = f"{safe_id}@users.invalid"

        if frappe.db.exists("User", user_id):
            frappe.throw(_("This internal User ID already exists."))

        if frappe.db.exists("User", {"mobile_no": mobile}):
            frappe.throw(_("This mobile number is already assigned to a User."))

        user = frappe.new_doc("User")
        user.update({
            "email": user_id,
            "first_name": emp.employee_name or emp.name,
            "mobile_no": mobile,
            "phone": mobile,
            "user_type": "System User",
            "enabled": 1,
            "send_welcome_email": 0,
        })

        user.append("roles", {"role": "Employee Self Service"})

        # Link before inserting so Employee/User validation can resolve it.
        emp.db_set("user_id", user_id, update_modified=False)
        user.insert(ignore_permissions=True)

    # Synchronize account details from Employee.
    user.mobile_no = mobile
    user.phone = mobile
    user.role_profile_name = role_profile
    user.save(ignore_permissions=True)

    # Change password only when HR entered a new one.
    if password:
        update_password(user_id, password)

        # Clear the temporary password after successful update.
        emp.db_set("custom_password", "", update_modified=False)

    return {
        "user_id": user_id,
        "employee": emp.name,
        "mobile_no": mobile,
        "role_profile": role_profile,
        "message": _("User account and Role Profile synchronized."),
    }
