from enum import Enum, unique


@unique
class AuditTypes(Enum):

    # User account events
    create_user = "create_user"
    update_user = "update_user"
    invite_user = "invite_user"
    user_auth_failed = "user_auth_failed"
    contact_update = "contact_update"
    create_supplier = "create_supplier"
    supplier_update = "supplier_update"

    # Draft service lifecycle event
    create_draft_service = "create_draft_service"
    update_draft_service = "update_draft_service"
    update_draft_service_status = "update_draft_service_status"
    complete_draft_service = "complete_draft_service"
    publish_draft_service = "publish_draft_service"
    delete_draft_service = "delete_draft_service"

    # Live service lifecycle events
    import_service = "import_service"
    update_service = "update_service"
    update_pending_service = "update_pending_service"
    reject_pending_service = "reject_pending_service"
    update_service_admin = "update_service_admin"
    update_service_status = "update_service_status"
    update_service_supplier = "update_service_supplier"

    # Brief lifecycle events
    create_brief = "create_brief"
    update_brief = "update_brief"
    update_brief_status = "update_brief_status"
    create_brief_response = "create_brief_response"
    update_brief_response = "update_brief_response"
    submit_brief_response = "submit_brief_response"
    add_brief_clarification_question = "add_brief_clarification_question"
    delete_brief = "delete_brief"
    update_brief_framework_id = "update_brief_framework_id"

    # Supplier actions
    register_framework_interest = "register_framework_interest"
    view_clarification_questions = "view_clarification_questions"
    send_clarification_question = "send_clarification_question"
    send_application_question = "send_application_question"
    answer_selection_questions = "answer_selection_questions"
    update_declaration_answers = "update_declaration_answers"
    agree_framework_variation = "agree_framework_variation"
    update_supplier_framework = "update_supplier_framework"
    supplier_central_digital_platform_connection_created = "supplier_central_digital_platform_connection_created"
    supplier_central_digital_platform_connection_revoked = "supplier_central_digital_platform_connection_revoked"
    supplier_central_digital_platform_data_updated = "supplier_central_digital_platform_data_updated"
    contact_update_from_central_digital_platform = "contact_update_from_central_digital_platform"
    set_fvra_result = "set_fvra_result"
    update_fvra_answers = "update_fvra_answers"
    set_evaluation_scores = 'set_evaluation_scores'
    update_evaluation_scores = 'update_evaluation_scores'

    # Framework agreements
    create_agreement = "create_agreement"
    update_agreement = "update_agreement"
    upload_signed_agreement = "upload_signed_agreement"
    sign_agreement = "sign_agreement"
    upload_countersigned_agreement = "upload_countersigned_agreement"
    countersign_agreement = "countersign_agreement"
    delete_countersigned_agreement = "delete_countersigned_agreement"
    delete_supplier_framework_declaration = "delete_supplier_framework_declaration"
    supplier_framework_central_digital_platform_data_updated = \
        "supplier_framework_central_digital_platform_data_updated"

    # Framework lifecycle
    create_framework = "create_framework"
    framework_update = "framework_update"
    create_framework_communication_category = "create_framework_communication_category"
    update_framework_communication_category = "update_framework_communication_category"
    delete_framework_communication_category = "delete_framework_communication_category"

    # Admin actions
    snapshot_framework_stats = "snapshot_framework_stats"
    create_buyer_email_domain = "create_buyer_email_domain"
    delete_buyer_email_domain = "delete_buyer_email_domain"

    # Projects
    create_project = "create_project"
    create_project_search = "create_project_search"
    lock_project = "lock_project"
    downloaded_project = "downloaded_project"
    update_project = "update_project"

    # Outcomes
    create_outcome = "create_outcome"
    complete_outcome = "complete_outcome"
    update_outcome = "update_outcome"

    # Mailing list actions
    mailing_list_subscription = "mailing_list_subscription"

    # Communications
    create_communication = "create_communication"
    update_communication = "update_communication"
    resolve_communication = "resolve_communication"
    undo_resolve_communication = "undo_resolve_communication"
    send_communication_message = "send_communication_message"
    read_communication_message = "read_communication_message"

    # System message
    create_system_message = "create_system_message"
    update_system_message = "update_system_message"

    # Lot questions responses
    create_lot_questions_response = "create_lot_questions_response"
    update_lot_questions_response_answers = "update_lot_questions_response_answers"
    complete_lot_questions_response = "complete_lot_questions_response"

    create_lot_questions_response_section_evaluation = "create_lot_questions_response_section_evaluation"
    update_lot_questions_response_section_evaluation = "update_lot_questions_response_section_evaluation"

    # Evaluations
    update_evaluator_framework_lot_assignment_status = "update_evaluator_framework_lot_assignment_status"
    create_evaluator_framework_lot = "create_evaluator_framework_lot"
    update_evaluator_framework_lot_status = "update_evaluator_framework_lot_status"
    create_evaluator_framework_lot_section = "create_evaluator_framework_lot_section"
    update_evaluator_framework_lot_section_status = "update_evaluator_framework_lot_section_status"
    update_evaluator_framework_lot_section_assignment_status = \
        "update_evaluator_framework_lot_section_assignment_status"

    create_evaluator_framework_lot_section_evaluation = "create_evaluator_framework_lot_section_evaluation"
    update_evaluator_framework_lot_section_evaluation = "update_evaluator_framework_lot_section_evaluation"

    # Migrate supplier
    migrate_supplier = "migrate_supplier"

    # Technical award certificate
    create_technical_ability_certificate = "create_technical_ability_certificate"
    update_technical_ability_certificate_answers = "update_technical_ability_certificate_answers"
    send_technical_ability_certificate = "send_technical_ability_certificate"
    revert_technical_ability_certificate_to_in_progress = "revert_technical_ability_certificate_to_in_progress"
    approve_technical_ability_certificate = "approve_technical_ability_certificate"
    technical_ability_certificate_auth_failed = "technical_ability_certificate_auth_failed"

    # Lot questions responses
    create_lot_pricing = "create_lot_pricing"
    update_lot_pricing_answers = "update_lot_pricing_answers"
    complete_lot_pricing = "complete_lot_pricing"

    # Tasks
    register_task_creation = "register_task_creation"
    register_task_success = "register_task_success"
    register_task_failure = "register_task_failure"

    @staticmethod
    def is_valid_audit_type(test_audit_type):

        for name, audit_type in AuditTypes.__members__.items():
            if audit_type.value == test_audit_type:
                return True
        return False
