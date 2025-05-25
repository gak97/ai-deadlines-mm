## AI Deadlines [![Build Status](https://travis-ci.com/abhshkdz/ai-deadlines.svg?branch=gh-pages)](https://travis-ci.com/abhshkdz/ai-deadlines)

Countdown timers to keep track of a bunch of CV/NLP/ML/RO conference deadlines.

## Contributing

[![](https://sourcerer.io/fame/abhshkdz/abhshkdz/ai-deadlines/images/0)](https://sourcerer.io/fame/abhshkdz/abhshkdz/ai-deadlines/links/0)[![](https://sourcerer.io/fame/abhshkdz/abhshkdz/ai-deadlines/images/1)](https://sourcerer.io/fame/abhshkdz/abhshkdz/ai-deadlines/links/1)[![](https://sourcerer.io/fame/abhshkdz/abhshkdz/ai-deadlines/images/2)](https://sourcerer.io/fame/abhshkdz/abhshkdz/ai-deadlines/links/2)[![](https://sourcerer.io/fame/abhshkdz/abhshkdz/ai-deadlines/images/3)](https://sourcerer.io/fame/abhshkdz/abhshkdz/ai-deadlines/links/3)[![](https://sourcerer.io/fame/abhshkdz/abhshkdz/ai-deadlines/images/4)](https://sourcerer.io/fame/abhshkdz/abhshkdz/ai-deadlines/links/4)[![](https://sourcerer.io/fame/abhshkdz/abhshkdz/ai-deadlines/images/5)](https://sourcerer.io/fame/abhshkdz/abhshkdz/ai-deadlines/links/5)[![](https://sourcerer.io/fame/abhshkdz/abhshkdz/ai-deadlines/images/6)](https://sourcerer.io/fame/abhshkdz/abhshkdz/ai-deadlines/links/6)[![](https://sourcerer.io/fame/abhshkdz/abhshkdz/ai-deadlines/images/7)](https://sourcerer.io/fame/abhshkdz/abhshkdz/ai-deadlines/links/7)

Contributions are very welcome!

To keep things minimal, I'm only looking to list top-tier conferences in AI as per [conferenceranks.com][6] and my judgement calls. Please feel free to maintain a separate fork if you don't see your sub-field or conference of interest listed.

To add or update a deadline:
- Fork the repository
- Update `_data/conferences.yml`
- Make sure it has the `title`, `year`, `id`, `link`, `deadline`, `timezone`, `date`, `place`, `sub` attributes
    + See available timezone strings [here](https://momentjs.com/timezone/).
- Optionally add a `note` and `abstract_deadline` in case the conference has a separate mandatory abstract deadline
- Optionally add `hindex` (refers to h5-index from [here](https://scholar.google.com/citations?view_op=top_venues&vq=eng))
- Example:
    ```yaml
    - title: BestConf
      year: 2022
      id: bestconf22  # title as lower case + last two digits of year
      full_name: Best Conference for Anything  # full conference name
      link: link-to-website.com
      deadline: YYYY-MM-DD HH:SS
      abstract_deadline: YYYY-MM-DD HH:SS
      timezone: Asia/Seoul
      place: Incheon, South Korea
      date: September, 18-22, 2022
      start: YYYY-MM-DD
      end: YYYY-MM-DD
      paperslink: link-to-full-paper-list.com
      pwclink: link-to-papers-with-code.com
      hindex: 100.0
      sub: SP
      note: Important
    ```
- Send a pull request

## Automated Conference Updates

The conference data in `_data/conferences.yml` is now periodically updated by an automated process. This system is designed to help keep conference information current and reduce manual effort. Here’s how it works:

-   **Script**: A Python script named `update_conferences.py` (located in the root directory) is responsible for fetching new data. It attempts to find official conference websites and scrape relevant information, such as deadlines, dates, and locations.
-   **Automation**: A GitHub Actions workflow (defined in `.github/workflows/update_data.yml`) executes this script automatically on the first day of every month. If the script finds any new or updated conference information, the workflow commits these changes to the `_data/conferences.yml` file.
-   **Scope**: The script primarily focuses on updating information for conferences already listed in `_data/conferences.yml` or finding details for their future editions (e.g., if NeurIPS 2025 is listed, it will try to find NeurIPS 2026 and 2027).
-   **Accuracy**: While the script aims for accuracy, automated web scraping can be imperfect. There might be instances where the scraped data is not entirely correct or complete.
-   **Manual Edits & Overwrites**: If you manually edit entries in `_data/conferences.yml` that the script also manages (identified by a combination of conference `title` and `year`, which forms the `id`), your changes might be overwritten. The script will update entries based on what it finds. If you make manual changes to an entry that the script is likely to find (e.g., a future edition of a known conference), be aware that the script might revert these changes if it scrapes conflicting information. For conferences not typically found by the script (e.g., very niche or new conferences not yet in the base list), manual additions are less likely to be affected by automated overwrites.

We hope this automated system enhances the timeliness and accuracy of the conference data. Contributions and corrections are still welcome, especially for information the script might miss or misinterpret.

## Forks & other useful listings

- [geodeadlin.es][3] by @LukasMosser
- [neuro-deadlines][4] by @tbryn
- [ai-challenge-deadlines][5] by @dieg0as
- [CV-oriented ai-deadlines (with an emphasis on medical images)][8] by @duducheng
- [es-deadlines (Embedded Systems, Computer Architecture, and Cyber-physical Systems)][9] by @AlexVonB and @k0nze
- [2019-2020 International Conferences in AI, CV, DM, NLP and Robotics][10] by @JackieTseng
- [ccf-deadlines][11] by @ccfddl
- [networking-deadlines (Computer Networking, Measurement)][12] by @andrewcchu
- [ad-deadlines.com][13] by @daniel-bogdoll
- [sec-deadlines.github.io/ (Security and Privacy)][14] by @clementfung
- [pythondeadlin.es][15] by @jesperdramsch
- [deadlines.openlifescience.ai (Healthcare domain conferences and workshops)][16] by @monk1337
- [hci-deadlines.github.io (Human-Computer Interaction conferences)][17] by @makinteract
- [ds-deadlines.github.io (Distributed Systems, Event-based Systems, Performance, and Software Engineering conferences)][18] by @ds-deadlines
- [https://deadlines.cpusec.org/ (Computer Architecture-Security conferences)][19] by @hoseinyavarzadeh
- [se-deadlines.github.io (Software engineering conferences)][20] by @sivanahamer and @imranur-rahman
- [awesome-mlss (Machine Learning Summer Schools)][21] by @sshkhr and @gmberton

## License

This project is licensed under [MIT][1].

It uses:

- [IcoMoon Icons](https://icomoon.io/#icons-icomoon): [GPL](http://www.gnu.org/licenses/gpl.html) / [CC BY4.0](http://creativecommons.org/licenses/by/4.0/)

[1]: https://abhshkdz.mit-license.org/
[2]: http://aideadlin.es/
[3]: https://github.com/LukasMosser/geo-deadlines
[4]: https://github.com/tbryn/neuro-deadlines
[5]: https://github.com/dieg0as/ai-challenge-deadlines
[6]: http://www.conferenceranks.com/#
[8]: https://m3dv.github.io/ai-deadlines/
[9]: https://ekut-es.github.io/es-deadlines/
[10]: https://jackietseng.github.io/conference_call_for_paper/conferences.html
[11]: https://ccfddl.github.io/
[12]: https://noise-lab.net/networking-deadlines/
[13]: https://ad-deadlines.com/
[14]: https://sec-deadlines.github.io/
[15]: https://pythondeadlin.es/
[16]: https://deadlines.openlifescience.ai/
[17]: https://hci-deadlines.github.io/
[18]: https://ds-deadlines.github.io
[19]: https://deadlines.cpusec.org/
[20]: https://se-deadlines.github.io/
[21]: https://awesome-mlss.com/