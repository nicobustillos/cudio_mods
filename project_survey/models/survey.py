from odoo import fields, models
from odoo.http import request


class SurveyInvite(models.TransientModel):
    _inherit = 'survey.invite'

    task_id = fields.Many2one('project.task', string="Related Task")

    def _compute_survey_start_url(self):
        super()._compute_survey_start_url()
        for invite in self:
            if invite.survey_start_url and invite.task_id:
                sep = '&' if '?' in invite.survey_start_url else '?'
                invite.survey_start_url += f"{sep}task_id={invite.task_id.id}"

    def _prepare_answers(self, partners, emails):
        answers = super()._prepare_answers(partners, emails)
        if self.task_id:
            answers.write({'task_id': self.task_id.id})
        return answers


class SurveySurvey(models.Model):
    _inherit = 'survey.survey'

    def _create_answer(self, user=False, partner=False, email=False, test_entry=False, check_attempts=True, **additional_vals):
        """ Override to capture task_id from request params if available. Otherwise, survey created from just the generic URL, don't pass task_id """
        if not additional_vals.get('task_id') and request and request.params.get('task_id'):
            try:
                task_id = int(request.params.get('task_id'))
                # Verify existence
                if self.env['project.task'].browse(task_id).exists():
                    additional_vals['task_id'] = task_id
            except (ValueError, TypeError):
                pass
        
        return super()._create_answer(user=user, partner=partner, email=email, test_entry=test_entry, check_attempts=check_attempts, **additional_vals)


class SurveyAnswer(models.Model):
    _inherit = 'survey.question.answer'

    activity_type_id = fields.Many2one('mail.activity.type', string='Task Activity trigger', help="Activity type to trigger when this answer is selected on a Task.")


class SurveyUserInput(models.Model):
    _inherit = 'survey.user_input'

    task_id = fields.Many2one('project.task', string="Related Task", readonly=True)

    def _mark_done(self):
        res = super()._mark_done()
        for user_input in self:
            if user_input.task_id:
                user_input.task_id.message_post(
                    body=f"The customer has completed the survey '{user_input.survey_id.title}' for this task.",
                    subtype_xmlid='mail.mt_comment'
                )
                for line in user_input.user_input_line_ids:
                    if line.suggested_answer_id and line.suggested_answer_id.activity_type_id:
                        activity = user_input.task_id.activity_schedule(
                            activity_type_id=line.suggested_answer_id.activity_type_id.id,
                            user_id=user_input.task_id.user_ids[0] and user_input.task_id.user_ids[0].id or user_input.task_id.create_uid.id,
                            summary=f"Follow-up requested: {user_input.survey_id.title}",
                            note=f"The customer has requested a follow-up based on survey '{user_input.survey_id.title}'.",
                        )

        return res