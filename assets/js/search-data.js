// get the ninja-keys element
const ninja = document.querySelector('ninja-keys');

// add the home and posts menu items
ninja.data = [{
    id: "nav-about",
    title: "about",
    section: "Navigation",
    handler: () => {
      window.location.href = "/";
    },
  },{id: "nav-publications",
          title: "publications",
          description: "",
          section: "Navigation",
          handler: () => {
            window.location.href = "/publications/";
          },
        },{id: "nav-courses",
          title: "courses",
          description: "",
          section: "Navigation",
          handler: () => {
            window.location.href = "/courses/";
          },
        },{id: "nav-lab",
          title: "lab",
          description: "",
          section: "Navigation",
          handler: () => {
            window.location.href = "/lab/";
          },
        },{id: "nav-cv",
          title: "cv",
          description: "",
          section: "Navigation",
          handler: () => {
            window.location.href = "/cv/";
          },
        },{id: "books-the-godfather",
          title: 'The Godfather',
          description: "",
          section: "Books",handler: () => {
              window.location.href = "/books/the_godfather/";
            },},{id: "courses-electromagnetic-theory",
          title: 'Electromagnetic Theory',
          description: "graduate course",
          section: "Courses",handler: () => {
              window.location.href = "/courses/course_emt/";
            },},{id: "courses-fourier-transform",
          title: 'Fourier Transform',
          description: "graduate course",
          section: "Courses",handler: () => {
              window.location.href = "/courses/course_fourier/";
            },},{id: "courses-geometrical-theory-of-diffraction",
          title: 'Geometrical Theory of Diffraction',
          description: "graduate course",
          section: "Courses",handler: () => {
              window.location.href = "/courses/course_gtd/";
            },},{id: "courses-antenna-theory-fundamentals",
          title: 'Antenna Theory Fundamentals',
          description: "",
          section: "Courses",handler: () => {
              window.location.href = "/courses/talk_antenna/";
            },},{id: "courses-introduction-to-julia-programming",
          title: 'Introduction to Julia Programming',
          description: "",
          section: "Courses",handler: () => {
              window.location.href = "/courses/talk_julia/";
            },},{id: "courses-introduction-to-pstd",
          title: 'Introduction to PSTD',
          description: "",
          section: "Courses",handler: () => {
              window.location.href = "/courses/talk_pstd/";
            },},{id: "courses-reflectarray-design-via-sdm",
          title: 'Reflectarray Design via SDM',
          description: "",
          section: "Courses",handler: () => {
              window.location.href = "/courses/talk_reflectarray/";
            },},{id: "news-a-simple-inline-announcement",
          title: 'A simple inline announcement.',
          description: "",
          section: "News",},{id: "news-a-long-announcement-with-details",
          title: 'A long announcement with details',
          description: "",
          section: "News",handler: () => {
              window.location.href = "/news/announcement_2/";
            },},{id: "news-a-simple-inline-announcement-with-markdown-emoji-sparkles-smile",
          title: 'A simple inline announcement with Markdown emoji! :sparkles: :smile:',
          description: "",
          section: "News",},{
        id: 'social-email',
        title: 'email',
        section: 'Socials',
        handler: () => {
          window.open("mailto:%6A%77%6C%69%75@%6E%74%75%74.%65%64%75.%74%77", "_blank");
        },
      },{
        id: 'social-github',
        title: 'GitHub',
        section: 'Socials',
        handler: () => {
          window.open("https://github.com/jake-w-liu", "_blank");
        },
      },{
        id: 'social-orcid',
        title: 'ORCID',
        section: 'Socials',
        handler: () => {
          window.open("https://orcid.org/0000-0001-5458-7917", "_blank");
        },
      },{
      id: 'light-theme',
      title: 'Change theme to light',
      description: 'Change the theme of the site to Light',
      section: 'Theme',
      handler: () => {
        setThemeSetting("light");
      },
    },
    {
      id: 'dark-theme',
      title: 'Change theme to dark',
      description: 'Change the theme of the site to Dark',
      section: 'Theme',
      handler: () => {
        setThemeSetting("dark");
      },
    },
    {
      id: 'system-theme',
      title: 'Use system default theme',
      description: 'Change the theme of the site to System Default',
      section: 'Theme',
      handler: () => {
        setThemeSetting("system");
      },
    },];
