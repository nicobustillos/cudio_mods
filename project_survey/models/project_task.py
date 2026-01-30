from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ProjectTaskStage(models.Model):
    _inherit = 'project.task.type'

    survey_id = fields.Many2one('survey.survey', string="Survey to send", 
        help="If set, this survey can be sent to the customer from the task when it is in this stage.")


class ProjectTask(models.Model):
    _inherit = 'project.task'

    survey_input_ids = fields.One2many('survey.user_input', 'task_id', string="Survey Answers")
    survey_input_count = fields.Integer(compute='_compute_survey_input_count')
    survey_avg_score = fields.Float(compute='_compute_survey_input_count', string="Avg. Score")
    survey_id = fields.Many2one(related='stage_id.survey_id', string="Stage Survey", readonly=True)

    @api.depends('survey_input_ids', 'survey_input_ids.scoring_total', 'survey_input_ids.state')
    def _compute_survey_input_count(self):
        for task in self:
            completed_surveys = task.survey_input_ids.filtered(lambda s: s.state == 'done')
            task.survey_input_count = len(completed_surveys)
            if completed_surveys:
                task.survey_avg_score = sum(completed_surveys.mapped('scoring_percentage')) / len(completed_surveys)
            else:
                task.survey_avg_score = 0.0

    def action_send_survey(self):
        self.ensure_one()
        survey = self.stage_id.survey_id
        if not survey:
            raise UserError(_("There is no survey defined for this task stage."))
        if not self.partner_id:
            raise UserError(_("There is no Customer defined for this task."))
        
        # We just invoke the same wizard that is shown from the survey native form
        return {
            'name': _("Send Survey"),
            'type': 'ir.actions.act_window',
            'res_model': 'survey.invite',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_survey_id': survey.id,
                'default_task_id': self.id,
                'default_partner_ids': [self.partner_id.id] if self.partner_id else [],
            },
        }

    def action_view_survey_results(self):
        self.ensure_one()
        return {
            'name': _("Survey Results"),
            'type': 'ir.actions.act_window',
            'res_model': 'survey.user_input',
            'view_mode': 'list,form',
            'domain': [('task_id', '=', self.id)],
            'context': {'default_task_id': self.id},
        }
