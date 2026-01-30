from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError

class TestProjectSurvey(TransactionCase):

    def setUp(self):
        super(TestProjectSurvey, self).setUp()
        self.ProjectTask = self.env['project.task']
        self.ProjectStage = self.env['project.task.type']
        self.Survey = self.env['survey.survey']
        self.Partner = self.env['res.partner']

        # Create a survey
        self.survey = self.Survey.create({
            'title': 'Customer Feedback Survey',
        })

        # Create a project
        self.project = self.env['project.project'].create({
            'name': 'Test Project',
        })

        # Create a stage with survey linked to project
        self.stage_with_survey = self.ProjectStage.create({
            'name': 'Done',
            'survey_id': self.survey.id,
            'project_ids': [(4, self.project.id)],
        })

        # Create a customer
        self.customer = self.Partner.create({
            'name': 'Test Customer',
            'email': 'customer@example.com',
        })

        # Create a task
        self.task = self.ProjectTask.create({
            'name': 'Test Task',
            'project_id': self.project.id,
            'stage_id': self.stage_with_survey.id,
            'partner_id': self.customer.id,
        })

    def test_send_survey_action(self):
        """ Test that action_send_survey opens the wizard with correct context """
        action = self.task.action_send_survey()
        
        self.assertEqual(action['res_model'], 'survey.invite')
        self.assertEqual(action['context']['default_survey_id'], self.survey.id)
        self.assertEqual(action['context']['default_task_id'], self.task.id)
        self.assertEqual(action['context']['default_partner_ids'], [self.customer.id])

    def test_survey_invite_creation(self):
        """ Test that creating survey invite creates survey.user_input linked to task """
        
        # Simulate opening wizard
        wizard = self.env['survey.invite'].with_context(
            default_survey_id=self.survey.id,
            default_task_id=self.task.id,
            default_partner_ids=[self.customer.id]
        ).create({'subject': 'Test Subject'})

        # Send invite (creates answers)
        # Note: We can also call create_invite directly but usually UI calls action_invite or similar?
        # survey.invite usually works by creating the record then calling action_invite?
        # Actually in the code `create_invite` didn't exist in the file I read!
        # `survey.invite` has `action_invite`.
        
        # Wait, I used `create_invite` in my plan and my override in `models/survey_invite.py`.
        # I need to check `survey_invite.py` content again.
        # It had `action_invite`.
        # It did NOT have `create_invite`. `create_invite` was my hallucination or mixed up with another wizard.
        # I must fix `models/survey_invite.py`.
        
        # Checking file content from previous turn...
        # Line 263: def action_invite(self):
        # There is no `create_invite`.
        
        # So my override in `models/survey_invite.py` using `create_invite` won't work if it's not called.
        # Odoo wizards are usually created then a method is called.
        # However, `action_invite` calls `_prepare_answers`.
        # And I overrode `_prepare_answers`.
        # So as long as `_prepare_answers` is called, it's fine.
        
        # Let's verify `action_invite` calls `_prepare_answers`.
        # Line 291: `answers = self._prepare_answers(valid_partners, valid_emails)`
        # Yes.
        
        # So I only need `_prepare_answers` override.
        # I should remove `create_invite` from `models/survey_invite.py` if I added it?
        # I didn't add `create_invite` in the final `models/survey_invite.py` write (Step 34).
        # I only added `_prepare_answers`. Good.
        
        wizard.action_invite()
        
        # Check if answer was created and linked
        answer = self.env['survey.user_input'].search([
            ('survey_id', '=', self.survey.id),
            ('partner_id', '=', self.customer.id)
        ], limit=1)
        
        self.assertTrue(answer, "Survey answer should be created")
        self.assertEqual(answer.task_id, self.task, "Answer should be linked to the task")

    def test_view_survey_results(self):
        """ Test smart button action """
        # Create a dummy answer linked to task
        self.env['survey.user_input'].create({
            'survey_id': self.survey.id,
            'task_id': self.task.id,
            'partner_id': self.customer.id,
        })
        
        action = self.task.action_view_survey_results()
        self.assertEqual(action['res_model'], 'survey.user_input')
        self.assertIn(('task_id', '=', self.task.id), action['domain'])

    def test_survey_completion_chatter(self):
        """ Test that completing a survey posts a message on the task """
        answer = self.env['survey.user_input'].create({
            'survey_id': self.survey.id,
            'task_id': self.task.id,
            'partner_id': self.customer.id,
            'state': 'in_progress',
        })
        
        # Mark done
        answer._mark_done()
        
        # Check chatter
        # In test mode, message_post might not commit but it creates message records?
        # Yes, message_ids should contain it.
        messages = self.task.message_ids
        self.assertTrue(messages.filtered(lambda m: "has completed" in m.body), "Should create a chatter message")

