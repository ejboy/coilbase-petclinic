@param String lang
@param java.util.ResourceBundle messages
@param gg.jte.Content content
<!doctype html>
<html lang="${lang}">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>PetClinic</title>
    <link rel="icon" href="/resources/images/favicon.png">
    <link rel="stylesheet" href="/resources/css/petclinic.css">
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark" aria-label="${messages.getString("navigation")}">
        <div class="container-fluid">
            <a class="navbar-brand" href="/" aria-label="PetClinic"><span aria-hidden="true"></span></a>
            <div class="navbar-nav">
                <a class="nav-link" href="/">${messages.getString("home")}</a>
                <a class="nav-link" href="/owners/find">${messages.getString("findOwners")}</a>
                <a class="nav-link" href="/vets.html">${messages.getString("vets")}</a>
                <a class="nav-link" href="/oups">${messages.getString("error")}</a>
            </div>
        </div>
    </nav>
    <main class="container xd-container mb-3">${content}</main>
    <footer class="container xd-container small text-muted text-center mt-0 mb-3">
        <a href="https://github.com/PVRLabs/coilbase"><img src="/resources/images/coilbase-monochrome.svg" alt="CoilBase" width="150"></a><br>
        PetClinic running on <a href="https://github.com/PVRLabs/coilbase">CoilBase</a> · Based on <a href="https://github.com/spring-projects/spring-petclinic">Spring PetClinic</a>
    </footer>
</body>
</html>
