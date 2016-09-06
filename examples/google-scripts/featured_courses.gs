function createStepikMenu(e) {
  SpreadsheetApp.getUi()
    .createMenu('Stepik')
    .addItem('Featured Courses', 'collectFeaturedCoursesInfo')
    .addToUi();
}

function collectFeaturedCoursesInfo()
{
  newSheet = createOrReplaceSheet('Featured Courses')
  newSheet.appendRow(['ID', 'Title', 'Course Format', 'Target Audience', 'Workload']);
  newSheet.getRange(1, 1, 1, 5).setFontWeight('bold')
  page = 1
  do {
    response = getApiRequest('courses?is_featured=True&page=' + page);
    response_json = JSON.parse(response);
    data = response_json['courses'];
    for(id in data) {
      item = data[id]
      url = '=HYPERLINK("https://stepik.org/course/'+ item.id +'"; "'+ item.id +'")'
      newSheet.appendRow([url, item.title, item.course_format, item.target_audience, item.workload]);
    }
    page++;
  } while(response_json['meta']['has_next']); 
}

function createOrReplaceSheet(sheetName){
  app = SpreadsheetApp.getActive()
  oldSheet = app.getSheetByName(sheetName);
  if(oldSheet) {
    app.deleteSheet(oldSheet);
  }
  newSheet = app.insertSheet(sheetName);
  return newSheet
}
