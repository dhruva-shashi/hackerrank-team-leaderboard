def htmlize_leaderboard(json_content):
    if not json_content['ok']:
        return 'Error occured'

    contest_url = 'https://hackerrank.com/contests/'+json_content['contest_slug']
    last_updated = json_content['last_updated']

    html_text = '''
        <html>
            <head>
                <title>'''+json_content['contest_name']+'''</title>
                <style>
                    body {
                        font-family: verdana, sans-serif;
                        text-align: center;
                    }
                    
                    #contest-name {
                        margin-top: 50px;
                        font-weight: bold;
                        font-size: 32px;
                    }
                    
                    #contest-link {
                        margin-top: 50px;
                    }
                    
                    #last-updated {
                        margin-top: 20px;
                    }
                    
                    table {
                        margin-top: 50px;
                        margin-left: auto;
                        margin-right: auto;
                        margin-bottom: 100px;
                    }
                    
                    th, td {
                        padding: 5px;
                        padding-left: 20px;
                        padding-right: 20px;
                    }
                    
                    tr:nth-child(odd) {
                        background-color: #e8e8e8;
                    }
                    
                    .team-members {
                        font-size: 12px;
                        margin-top: 5px;
                    }
                    
                    .team-info {
                        max-width: 250px;
                    }
                    
                    .problem-link {
                        color: #FFFFFF;
                    }
                    
                    .right {
                        text-align: right;
                    }
                </style>
            </head>
        
            <body>
                <div id="contest-name">
                    '''+json_content['contest_name']+'''
                </div>
                
                <div id="contest-link">
                    Contest Link: <a href="'''+contest_url+'">'+contest_url+'''</a>
                </div>
                
                <div id="last-updated">
                    Last Updated: '''+str(last_updated)+'''
                </div>
                
                <div id="content">
                    <table>
                        <tr style="background-color: #000000;color: #ffffff;">
                            <th>Rank</th>
                            <th>Team</th>
                '''

    problem_url = 'https://hackerrank.com/contests/'+json_content['contest_slug']+'/challenges/'

    # Write the field names of the table and include a link for each problem
    i = 0
    for problem_slug in json_content['problem_slugs']:
        html_text += '<th><a class="problem-link" href="%s%s">%s</a></th>'%(problem_url, problem_slug, chr(i+ord('A')))
        i += 1

    html_text += '<th>Total Score</th><th>Time Taken</th></tr>'

    # Write the leaderboard, which includes, teamname, usernames of team members, points and time taken

    leaderboard = json_content['leaderboard']

    rank = 1
    for team in leaderboard:
        html_text += '<tr><td>'+str(rank)+'</td><td class="team-info"><div>'+team+'</div><div class="team-members">'

        for username in json_content['teams'][team]:
            html_text += '<a href="https://hackerrank.com/'+username+'">'+username+'</a>, '

        html_text += '</div></td>'
        rank += 1

        for problem in json_content['problem_slugs']:
            html_text += '<td class="right">'+str(leaderboard[team][0][problem])+'</td>'

        html_text += '<td class="right">%d</td><td class="right">%s</td></tr>'%(leaderboard[team][1], leaderboard[team][2])

    html_text += '''</table>
                </div>
            </body>
        </html>
    '''

    return html_text
