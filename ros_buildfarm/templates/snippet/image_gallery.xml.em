    <org.jenkinsci.plugins.imagegallery.ImageGalleryRecorder plugin="image-gallery@@1.4">
      <imageGalleries>
        <org.jenkinsci.plugins.imagegallery.imagegallery.ArchivedImagesGallery>
          <title>@(title)</title>
          <imageWidthText>@(image_width)</imageWidthText>
          <markBuildAsUnstableIfNoArchivesFound>false</markBuildAsUnstableIfNoArchivesFound>
          <includes>@(','.join(artifacts))</includes>
        </org.jenkinsci.plugins.imagegallery.imagegallery.ArchivedImagesGallery>
      </imageGalleries>
    </org.jenkinsci.plugins.imagegallery.ImageGalleryRecorder>
