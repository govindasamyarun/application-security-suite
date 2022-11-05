$(document).ready(function () {
  // Get settings value 
  var settings_data = $.get("/settings/data", function (returnedData) {
    $("#bitbucket_host_name").val(returnedData["bitbucket_host_name"]);
    $("#bitbucket_user_name").val(returnedData["bitbucket_user_name"]);
    $("#bitbucket_auth_token").val(returnedData["bitbucket_auth_token"]);
    $("#scan_all_branches").val(returnedData["scan_all_branches"]);
    $("#enable_slack_notifications").val(returnedData["enable_slack_notifications"]);
    $("#slack_host_name").val(returnedData["slack_host_name"]);
    $("#slack_auth_token").val(returnedData["slack_auth_token"]);
    $("#slack_channel_id").val(returnedData["slack_channel_id"]);
    $("#slack_message").val(returnedData["slack_message"]);
    $("#enable_jira_notifications").val(returnedData["enable_jira_notifications"]);
    $("#jira_host_name").val(returnedData["jira_host_name"]);
    $("#jira_epic_id").val(returnedData["jira_epic_id"]);
    $("#jira_user_name").val(returnedData["jira_user_name"]);
    $("#jira_auth_token").val(returnedData["jira_auth_token"]);
  }).fail(function () {
    console.log("Error");
  });
});

$(function () {
  $("#settingsbutton")
    .unbind()
    .click(function () {
      $("#updateModal").modal("show");
      $("#update_ok")
        .unbind()
        .click(function () {
          $("#updateModal").modal("hide");
          // Validation checks for bitbucket fields 
          if ($("#bitbucket_host_name").val() == "" || $("#bitbucket_user_name").val() == "" || $("#bitbucket_auth_token").val() == "" || $("#scan_all_branches").val() == "") {
            $("#updateModalStatus .modal-body").text('Enter bitbucket details');
            $("#updateModalStatus").modal("show");
              $("#update_ok_status")
                .unbind()
                .click(function () {
                  $("#updateModalStatus").modal("hide");
                });
            return;
          }

          // Validation checks for slack fields 
          if ($("#enable_slack_notifications").val() == "true" && ($("#slack_host_name").val() == "" || $("#slack_auth_token").val() == "" || $("#slack_channel_id").val() == "" || $("#slack_message").val() == "")) {
            $("#updateModalStatus .modal-body").text('Enter slack details');
            $("#updateModalStatus").modal("show");
              $("#update_ok_status")
                .unbind()
                .click(function () {
                  $("#updateModalStatus").modal("hide");
                });
            return;
          }

          // Validation checks for jira fields 
          if ($("#enable_jira_notifications").val() == "true" && ($("#jira_host_name").val() == "" || $("#jira_epic_id").val() == "" || $("#jira_user_name").val() == "" || $("#jira_auth_token").val() == "")) {
            $("#updateModalStatus .modal-body").text('Enter JIRA details');
            $("#updateModalStatus").modal("show");
              $("#update_ok_status")
                .unbind()
                .click(function () {
                  $("#updateModalStatus").modal("hide");
                });
            return;
          }
          $.fn.dataTable.Buttons.swfPath = "css/flashExport.swf";

          if (
            $("form#formsettings").serialize() ==
            "bitbucket_host_name=&bitbucket_user_name=&bitbucket_auth_token=&scan_all_branches=&enable_slack_notifications=&slack_host_name=&slack_auth_token=&slack_channel_id=&slack_message=&enable_jira_notifications=&jira_host_name=&jira_epic_id=&jira_user_name=&jira_auth_token="
          ) {
            $("#updateModalStatus .modal-body").text('Enter bitbucket details');
            $("#updateModalStatus").modal("show");
              $("#update_ok_status")
                .unbind()
                .click(function () {
                  $("#updateModalStatus").modal("hide");
                });
            return;
          }
          var params = { "bitbucketHost": $("#bitbucket_host_name").val(), "bitbucketUserName": $("#bitbucket_user_name").val(), "bitbucketAuthToken": $("#bitbucket_auth_token").val(), "scannerScanAllBranches": $("#scan_all_branches").val(), "slackEnable": $("#enable_slack_notifications").val(), "slackHost": $("#slack_host_name").val(), "slackAuthToken": $("#slack_auth_token").val(), "slackChannel": $("#slack_channel_id").val(), "slackMessage": $("#slack_message").val(), "jiraEnable": $("#enable_jira_notifications").val(), "jiraHost": $("#jira_host_name").val(), "jiraEpicID": $("#jira_epic_id").val(), "jiraUserName": $("#jira_user_name").val(), "jiraAuthToken": $("#jira_auth_token").val() }
          // Post data to the settings API 
          var newdata = $.post("/settings/data", params, function (returnedData) {
            if (returnedData['status'] == 'success') {
              $("#updateModalStatus .modal-body").text('Settings has been successfully updated');
              $("#updateModalStatus").modal("show");
              $("#update_ok_status")
                .unbind()
                .click(function () {
                  $("#updateModalStatus").modal("hide");
                  return returnedData;
                });
            } else {
              $("#updateModalStatusError").modal("show");
              $("#update_ok_status_error")
                .unbind()
                .click(function () {
                  $("#updateModalStatusError").modal("hide");
                  location.reload();
                });
            }
          }).fail(function () {
            $("#updateModalStatusError").modal("show");
            $("#update_ok_status_error")
              .unbind()
              .click(function () {
                $("#updateModalStatusError").modal("hide");
                location.reload();
              });
          });
        });
      $("#update_cancel")
        .unbind()
        .click(function () {
          $("#updateModal").modal("hide");
        });

    });
});