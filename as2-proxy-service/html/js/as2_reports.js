$(document).ready(function () {

  // This function handles the file download 
  function fileDownload(fURL, fName) {
    fetch(fURL)
      .then(response => {
        if (response.ok) {
          return response.blob().then(function (mBlob) {
            const url = window.URL.createObjectURL(mBlob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = url;
            a.download = fName;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
          })
        // Handle server errors 
        } else {
          return response.json().then(function (jsonError) {
            $("#mModalStatus").modal("show");
            $("#mModalMessageStatus").html("Error: Please contact administrator");
            $("#m_ok_status")
              .unbind()
              .click(function () {
                location.reload();
              });
          });
        }
      })
      .catch(err => {
        $("#mModalStatus").modal("show");
        $("#mModalMessageStatus").html("Error: Please contact administrator");
        $("#m_ok_status")
          .unbind()
          .click(function () {
            location.reload();
          });
      });
  }

  // Download button 
  $('#gldownloadreport').click(function (event) {
    event.preventDefault();
    fileDownload('/download/report', 'Gitleaks_Scan_Report.csv')
    return false;
  });

});
