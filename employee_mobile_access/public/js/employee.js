
// frappe.ui.form.on("Employee", {
//     refresh(frm) {
//         if (frm.is_new()) return;
//         if (frm.doc.user_id) return;
//         if (frm.doc.status !== "Active") return;

//         frm.add_custom_button(
//             __("Create Mobile Login"),
//             function () {
//                 if (!frm.doc.cell_number) {
//                     frappe.msgprint(
//                         __("Enter the employee's mobile number first.")
//                     );
//                     return;
//                 }

//                 frappe.confirm(
//                     __("Create a User account for this employee?"),
//                     function () {
//                         frappe.call({
//                             method:
//                                 "employee_mobile_access.api.create_user_for_employee",
//                             args: {
//                                 employee: frm.doc.name,
//                             },
//                             freeze: true,
//                             freeze_message: __("Creating User account..."),
//                             callback(r) {
//                                 if (r.message) {
//                                     frappe.msgprint({
//                                         title: __("Account Created"),
//                                         indicator: "green",
//                                         message: `
//                                             User ID: ${frappe.utils.escape_html(r.message.user_id)}<br>
//                                             Mobile: ${frappe.utils.escape_html(r.message.mobile_no)}
//                                         `,
//                                     });
//                                     frm.reload_doc();
//                                 }
//                             },
//                         });
//                     }
//                 );
//             }
//         );
//     },
// });



frappe.ui.form.on("Employee", {
    refresh(frm) {
        if (frm.is_new() || frm.doc.status !== "Active") return;

        const has_user = Boolean(frm.doc.user_id);

        frm.add_custom_button(
            has_user
                ? __("Update Login Settings")
                : __("Create Mobile Login"),
            function () {
                if (!frm.doc.cell_number) {
                    frappe.msgprint(
                        __("Please enter the employee's mobile number.")
                    );
                    return;
                }

                if (!frm.doc.custom_role_profile) {
                    frappe.msgprint(
                        __("Please select a Role Profile.")
                    );
                    return;
                }

                if (!has_user && !frm.doc.custom_password) {
                    frappe.msgprint(
                        __("Please enter a password in Custom Password.")
                    );
                    return;
                }

                const message = has_user
                    ? __("Update this user's password (if entered), mobile number and Role Profile?")
                    : __("Create a login account for this employee?");

                frappe.confirm(message, function () {
                    // Save pending Employee changes first.
                    const continue_sync = () => {
                        frappe.call({
                            method:
                                "employee_mobile_access.api.create_user_for_employee",
                            args: {
                                employee: frm.doc.name,
                            },
                            freeze: true,
                            freeze_message: __("Synchronizing User account..."),
                        }).then((r) => {
                            if (r.message) {
                                frappe.msgprint({
                                    title: __("Success"),
                                    indicator: "green",
                                    message: `
                                        ${frappe.utils.escape_html(r.message.message)}<br>
                                        User ID: ${frappe.utils.escape_html(r.message.user_id)}<br>
                                        Mobile: ${frappe.utils.escape_html(r.message.mobile_no)}<br>
                                        Role Profile: ${frappe.utils.escape_html(r.message.role_profile)}
                                    `,
                                });

                                frm.reload_doc();
                            }
                        });
                    };

                    if (frm.is_dirty()) {
                        frm.save().then(continue_sync);
                    } else {
                        continue_sync();
                    }
                });
            }
        );
    },
});

