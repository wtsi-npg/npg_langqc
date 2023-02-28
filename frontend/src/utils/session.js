// Get the user information from the apache OIDC module
// see https://github.com/zmartzone/mod_auth_openidc/wiki/Single-Page-Applications#session-info

export async function getUserName(answer) {
    await fetch(location.origin + "/login-redirect?info=json")
        .then((response) => {
            if (response.ok) {
                response.json()
                    .then((content) => {
                        let email = content.userinfo.email;
                        answer(email);
                    })
            }
        });
}
