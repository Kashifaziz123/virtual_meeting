# -*- coding: utf-8 -*-
import uuid
import hashlib
import requests
from xml.etree import ElementTree
from odoo import models, fields, api, exceptions


class UmlOnlineClass(models.Model):
    _inherit = 'calendar.event'

    # @api.model
    def _generate_uuid(self):
        return uuid.uuid1()

    # name --> meeting title
    # user_id  --> moderator_user_id
    # not required -> field with same name available
    # attendee_ids -> students
    start_datetime = fields.Datetime('Start DateTime', compute='_compute_dates', inverse='_inverse_dates', store=True,
                                     states={'done': [('readonly', True)]}, tracking=True,
                                     defult=lambda self: fields.datetime.now())
    user_id = fields.Many2one('res.users', 'Owner', required=True, states={'done': [('readonly', True)]}, default=lambda self: self.env.user)
    state = fields.Selection([('draft', 'Unconfirmed'), ('open', 'Confirmed'), ('in_progress', 'In Progress'),
                              ('done', 'Done')], string='Status', readonly=True, tracking=True, default='draft')
    isOnline = fields.Boolean(string="Online Meeting")
    allowStartStopRecording = fields.Boolean(string="Recording Enable")
    autoStartRecording = fields.Boolean(string="Auto Recording")
    webcamsOnlyForModerator = fields.Boolean(string="Webcams Visible Only To Moderator")
    send_mail = fields.Boolean(string="Send mail")
    welcome = fields.Char(string="Welcome Note")
    muteOnStart = fields.Boolean(string="Mute All On Start")
    allowModsToUnmuteUsers = fields.Boolean(string="Allow Moderators To Unmute Students")
    lockSettingsDisableMic = fields.Boolean(string="Disable Mic Of Students")
    # Compulsory
    meetingID = fields.Char(string="Online Session ID", readonly=True,default=_generate_uuid)
    attendeePW = fields.Char(string="Students Password")
    moderatorPW = fields.Char(string="Moderators Password")

    def get_bigblue_config(self):
        bigblue_secret_key = self.env['ir.config_parameter'].sudo().search([('key', '=', 'secret_key')])
        bigblue_url = self.env['ir.config_parameter'].sudo().search([('key', '=', 'url')])
        bigblue_logout_url = self.env['ir.config_parameter'].sudo().search([('key', '=', 'logout_url')])
        return bigblue_url.value, bigblue_secret_key.value, bigblue_logout_url.value if bigblue_secret_key and bigblue_url and bigblue_logout_url \
            else None

    @api.onchange('duration')
    def _verify_valid_duration(self):
        if self.duration < 0:
            return {
                'warning': {
                    'title': "Incorrect 'duration' value",
                    'message': "The duration of class can not be negative",
                },
            }

    # @api.multi
    def create_meeting(self):
        general_settings = self.get_bigblue_config()
        if self.duration == 0:
            checksums = "create" + "name=" + str(self.name).replace(" ", "%20") + "&meetingID=" + str(self.meetingID)\
                        + "&record=true&logoutURL="+str(general_settings[2])+"&webcamsOnlyForModerator="+str(self.webcamsOnlyForModerator)\
                        + "&autoStartRecording=" + str(self.autoStartRecording)\
                        + "&allowStartStopRecording=" + str(self.allowStartStopRecording) \
                        + "&welcome=" + str(self.welcome).replace(" ", "%20") + "&muteOnStart=" + str(self.muteOnStart) + "&allowModsToUnmuteUsers="\
                        + str(self.allowModsToUnmuteUsers) + "&lockSettingsDisableMic=" + str(self.lockSettingsDisableMic) + str(general_settings[1])
            checksum = hashlib.sha1(checksums.encode()).hexdigest()
            link = str(general_settings[0])+"create?name="+str(self.name)+"&meetingID="\
                   +str(self.meetingID)+"&record=true&logoutURL="+str(general_settings[2])+"&webcamsOnlyForModerator="+str(self.webcamsOnlyForModerator)\
                   +"&autoStartRecording="+str(self.autoStartRecording)+"&allowStartStopRecording="+str(self.allowStartStopRecording) \
                   + "&welcome=" + str(self.welcome).replace(" ", "%20") + "&muteOnStart=" + str(self.muteOnStart) + "&allowModsToUnmuteUsers=" \
                   + str(self.allowModsToUnmuteUsers) + "&lockSettingsDisableMic=" + str(self.lockSettingsDisableMic) \
                   +"&checksum="+checksum
        else:
            duration = str(self.duration).split('.')
            duration[0] = int(duration[0])*60 + int(duration[1])
            checksums = "create" + "name=" + str(self.name).replace(" ", "%20") + "&meetingID=" + str(self.meetingID)\
                        + "&record=true&logoutURL="+str(general_settings[2])+"&webcamsOnlyForModerator="+str(self.webcamsOnlyForModerator)\
                        + "&duration=" + str(duration[0]) + "&autoStartRecording=" + str(self.autoStartRecording)\
                        + "&allowStartStopRecording=" + str(self.allowStartStopRecording) \
                        + "&welcome=" + str(self.welcome).replace(" ", "%20") + "&muteOnStart=" + str(self.muteOnStart) + "&allowModsToUnmuteUsers=" \
                        + str(self.allowModsToUnmuteUsers) + "&lockSettingsDisableMic=" + str(self.lockSettingsDisableMic)\
                        + str(general_settings[1])
            checksum = hashlib.sha1(checksums.encode()).hexdigest()
            link = str(general_settings[0])+"create?name="+str(self.name).replace(" ", "%20")+"&meetingID="\
                   +str(self.meetingID)+"&record=true&logoutURL="+str(general_settings[2])+"&webcamsOnlyForModerator="+str(self.webcamsOnlyForModerator)\
                   +"&duration="+str(duration[0])+"&autoStartRecording="\
                   +str(self.autoStartRecording)+"&allowStartStopRecording="+str(self.allowStartStopRecording) \
                   + "&welcome=" + str(self.welcome).replace(" ", "%20") + "&muteOnStart=" + str(self.muteOnStart) + "&allowModsToUnmuteUsers=" \
                   + str(self.allowModsToUnmuteUsers) + "&lockSettingsDisableMic=" + str(self.lockSettingsDisableMic)\
                   +"&checksum="+checksum
        try:
            print(link)
            response = requests.get(link)
            Returns = ElementTree.fromstring(response.content)
        except:
            raise exceptions.AccessDenied("Server error\n Please try again in few minutes")
        if Returns[0].text == "SUCCESS":
            self.state = 'in_progress'
            self.attendeePW = Returns[4].text
            self.moderatorPW = Returns[5].text
            if self.send_mail:
                self.send_email_func()
        elif Returns[0].text == "FAILED":
            if Returns[1].text == "idNotUnique":
                self.state = 'in_progress'
            elif Returns[1].text == "checksumError":
                raise exceptions.AccessDenied("Error \nchecksum validation failed!")
            else:
                raise exceptions.AccessDenied("Undefined Error\n Kindly contact your administrator")
        else:
             raise exceptions.AccessDenied("Undefined Error\n Kindly contact your administrator")
        #     Return=""
        #     for child in Returns:
        #         Return+=str(child.tag)+"--"+str(child.text)+"\n"
        #     raise exceptions.ValidationError(checksums+"\n"+checksum+"\n"+link+"\n")
        # raise exceptions.ValidationError(Return)

    # @api.multi
    def join_meeting(self, person, name):
        general_settings = self.get_bigblue_config()
        link = ""
        if person == "moderator":
            checksum = "join"+"meetingID="+str(self.meetingID)+"&password="+str(self.moderatorPW)+"&fullName="\
                      +str(self.user_id.name).replace(" ","%20")+str(general_settings[1])
            checksum = hashlib.sha1(checksum.encode()).hexdigest()
            link = str(general_settings[0])+"join?meetingID=" + str(self.meetingID) + "&password="+ str(self.moderatorPW)\
                  +"&fullName="+str(self.user_id.name).replace(" ","%20") + "&checksum="+checksum
        # self.join_link_moderator = link
        elif person == "student":
            checksum = "join"+"meetingID="+str(self.meetingID)+"&password="+str(self.attendeePW)+"&fullName="\
                      +str(name).replace(" ","%20")+str(general_settings[1])
            checksum = hashlib.sha1(checksum.encode()).hexdigest()
            link = str(general_settings[0])+"join?meetingID=" + str(self.meetingID) + "&password="+ str(self.attendeePW)\
                  +"&fullName="+str(name).replace(" ","%20") + "&checksum="+checksum
        # self.join_link_student = link
        return link

    # @api.multi
    def download_recording(self):
        general_settings = self.get_bigblue_config()
        checksums = "getRecordings" + "meetingID=" + str(self.meetingID)+str(general_settings[1])
        checksum = hashlib.sha1(checksums.encode()).hexdigest()
        link = str(general_settings[0])+"getRecordings?meetingID="+str(self.meetingID)+"&checksum="+checksum

        try:
            response = requests.get(link)
            Returns = ElementTree.fromstring(response.content)
        except:
            raise exceptions.AccessDenied("Server error\n Please try again in few minutes")

        haschild = False
        for child in Returns[1]:
            haschild = True
            break
        if haschild:
            return {
                'type': 'ir.actions.act_url',
                'target': 'self',
                'url': Returns[1][0][13][0][1].text,
            }
        else:
            raise exceptions.AccessDenied("Server error !\n If recording was made then"
                                          "\n Try again in "+str(self.duration)+" minutes."
                                          "\n after the time of class ended")

    # @api.multi
    def join_meeting_url(self):
        general_settings = self.get_bigblue_config()
        checksum = "join" + "meetingID=" + str(self.meetingID) + "&password=" + str(self.moderatorPW) + "&fullName=" \
                   + str(self.user_id.name).replace(" ", "%20") + "&redirect=FALSE" + str(general_settings[1])
        checksum = hashlib.sha1(checksum.encode()).hexdigest()
        link = str(general_settings[0]) + "join?meetingID=" + str(self.meetingID) + "&password=" + str(self.moderatorPW) \
               + "&fullName=" + str(self.user_id.name).replace(" ", "%20") + "&redirect=FALSE" + "&checksum=" + checksum
        try:
            response = requests.get(link)
            Returns = ElementTree.fromstring(response.content)
            if Returns[0].text == "SUCCESS":
                if self.user_id.id == self.env.user.id:
                    return {
                        'type': 'ir.actions.act_url',
                        'target': 'new',
                        'url': self.join_meeting("moderator", ""),
                    }
                else:
                     return {
                        'type': 'ir.actions.act_url',
                        'target': 'new',
                        'url': self.join_meeting("student", self.env.user.name),
                    }
        except:
            raise exceptions.Warning("Meeting has already ended.")

    # @api.multi
    def delete_meeting(self):
        general_settings = self.get_bigblue_config()
        checksums = "end"+"meetingID="+str(self.meetingID)+"&password="+str(self.moderatorPW)+str(general_settings[1])
        checksum = hashlib.sha1(checksums.encode()).hexdigest()
        link = str(general_settings[0])+"end?meetingID="+str(self.meetingID)+"&password="+str(self.moderatorPW)+"&checksum="+checksum
        try:
            response = requests.get(link)
            Returns = ElementTree.fromstring(response.content)
        except:
            raise exceptions.AccessDenied("Server error\n Please try again in few minutes")

        if Returns[0].text == "SUCCESS":
            self.write({'state': 'done'})
        elif Returns[0].text == "FAILED":
            if Returns[1].text == "invalidPassword":
                raise exceptions.AccessDenied("System error !\n command not properly created.")
            elif Returns[1].text == "notFound":
                self.write({'state': 'done'})
            else:
                raise exceptions.AccessDenied("Undefined Error\n Kindly contact your administrator")
        else:
            raise exceptions.AccessDenied("Undefined Error\n Kindly contact your administrator")

    # @api.multi
    def copy(self, default=None):
        default = dict(default or {})
        default['meetingID'] = uuid.uuid1()
        return super(UmlOnlineClass, self).copy(default)

    # @api.multi
    def unlink(self):
        for data in self:
            if data.state not in 'draft':
                raise exceptions.UserError('Deleting is not possible when class is in progress or ended.')
        return super(UmlOnlineClass, self).unlink()

    # @api.multi
    def meeting_running(self):
        records = self.env['uml.online.class'].search([], limit=1, order='id desc')
        general_settings = self.get_bigblue_config()
        for data in records:
            if data.state == "in_progress":
                checksum = "join" + "meetingID=" + str(data.meetingID) + "&password=" + str(data.moderatorPW) + "&fullName=" \
                           + str(data.user_id.name).replace(" ", "%20") + "&redirect=FALSE" + str(general_settings[1])
                checksum = hashlib.sha1(checksum.encode()).hexdigest()
                link = str(general_settings[0]) + "join?meetingID=" + str(data.meetingID) + "&password=" + str(data.moderatorPW) \
                       + "&fullName=" + str(data.user_id.name).replace(" ", "%20") + "&redirect=FALSE" + "&checksum=" + checksum
                try:
                    response = requests.get(link)
                    Returns = ElementTree.fromstring(response.content)
                except:
                    data.state = 'done'

    def send_email_func(self):
        template_mod = self.env.ref('virtual_meeting.calendar_event_mail_moderator', False)
        template_stu = self.env.ref('virtual_meeting.calendar_event_mail_attendee', False)
        template_stu.subject = "Your Meeting " + str(self.name) + " Scheduled for " + str(self.start_datetime) \
                               + " has been started."
        template_mod.subject = "You have started the Meeting " + str(self.name) + " Scheduled for " +\
                               str(self.start_datetime) + "."
        template_mod.body_html = " \
                <div style='margin: 0px; padding: 0px;'>\
                    <p style='margin: 0px; padding: 0px; font-size: 13px;'>\
                        Dear " + self.user_id.name + "\
                        <br /><br />\
                        Here is your\
                        <br />\
                        link for your meeting " + str(self.join_meeting("moderator", ""))\
                    + "</p>\
                </div>"

        try:
            template_mod.email_to = self.user_id.email
            template_mod.send_mail(self.id, force_send=True)

            for attendee in self.attendee_ids:
                template_stu.email_to = attendee.email
                template_stu.body_html = " \
                    <div style='margin: 0px; padding: 0px;'>\
                        <p style='margin: 0px; padding: 0px; font-size: 13px;'>\
                            Dear " + attendee.partner_id.name + "\
                            <br /><br />\
                            Here is your\
                            <br />\
                            link for your meeting " + self.join_meeting("student", attendee.partner_id.name)\
                        + "</p>\
                    </div>"
                template_stu.send_mail(self.id, force_send=True)
        except:
            raise exceptions.Warning("Error sending mail.")

    # -----------------------------
    # -----------------------------
    # More Available fields for API
    # -----------------------------
    # -----------------------------
    # maxParticipants=fields.Integer(string="Students Count")
    # meta_Date=fields.Datetime(string="Date")
    # meta_Time=fields.Datetime(string="Time")
    # meta_Course=fields.Char(string="Course")
    # moderatorOnlyMessage=fields.Char(string="Welcome Note for Moderators")
