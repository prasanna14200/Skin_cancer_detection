# R2C Source Evidence Inventory

## Scope and source identity

This is a read-only audit of augmentation terminology and count definitions in the original paper. SHA-256 was checked before inspection:

`bac1b99167ad820232ecc6b47a3d562d2d9ca55ce19de36fba97b919e8aacee3`

The paper was inspected by parsing its page tree and decompressing PDF content streams with Node.js built-in `zlib`. Printed-page footers and page-tree order were used to map the page and stream objects. R2C did not render or visually inspect the full pages for the augmentation passages; their text below is recovered from the streams, not a visual transcription. Extracted line-wrap hyphenation has been joined. No statement is made that stream order itself proves paragraph layout.

## Source locators

| Evidence | Section | Printed page | Viewer page | Zero-based index | Page object | Stream object | Filter |
|---|---|---:|---:|---:|---:|---:|---|
| 13 techniques | G. IMPACT OF PREPROCESSING STEPS | 72869 | 18 | 17 | 181 | 182 | FlateDecode |
| 20 alternative methods | VI. CONCLUSION AND FUTURE WORK | 72872 | 21 | 20 | 469 | 534 | FlateDecode |
| Generic augmentation definition and symbolic transformation count | B. DATA AUGMENTATION | 72857 | 6 | 5 | 47 | 122 | FlateDecode |
| Image-level contrast enhancement | A. DATA PREPROCESSING (continued) | 72856 | 5 | 4 | 46 | 112 | FlateDecode |
| Crop operation before subsection B | A. DATA PREPROCESSING (continued) | 72857 | 6 | 5 | 47 | 122 | FlateDecode |
| Section IV-C split and reported totals | C. IMPLEMENTATION DETAIL | 72863 | 12 | 11 | 475 | 509 | FlateDecode |

### Section G: surrounding extracted context of the 13 reference

> "The color channels were corrected based on the Gray World algorithm, while the Retinex theory helped in preserving and enhancing the color and contrast information within the images. The comparison results of our novel color balancing technique using Peak Signal-to-Noise Ratio (PSNR), Mean Squared Error (MSE), and Structural Similarity Index (SSIM) with others is shown in Fig. 12. Higher PSNR values typically indicate better image quality and lower distortion. Similarly, MSE values indicate a smaller difference between the original and reconstructed images, and hence better quality. Further, SSIM values range from 0 to 1, with higher values indicating greater structural similarity between the original and reconstructed images. Finally, we employed thirteen data augmentation techniques on the 9-class dataset. This augmentation process introduced subtle variations in the Dermoscopic images, making the model more robust to different perspectives and reducing the risk of overfitting. The integration of these techniques in the current study suggests that their combination was effective in addressing color and data imbalances and also enhancing the quality of the Dermoscopic images."

The number 13 modifies "data augmentation techniques." This sentence explicitly scopes their use to the 9-class dataset. It provides no technique names.

### Section VI: surrounding extracted context of the 20 reference

> "In EG-VAN, EfficientNetV2S and modified ResNet50 work parallel with the Multi-Scale Feature Fusion (MFF) scheme to capture long-range dependencies and local feature patterns that are crucial for the accurate classification of skin lesions. Our SCGA module is spatially designed to capture spatial and contextual information and further explore the features of horizontal and vertical directions in the skin lesion. This approach not only enhances the model's ability to extract and process critical features but also improves computational efficiency, making it a promising solution for real-world applications in dermatology. To enhance the discriminative features of data and expand the training dataset, we additionally applied a hair-removing algorithm, color balancing method, and twenty alternative data augmentation methods. Our findings demonstrate that, on the 9-class dataset, our EG-VAN performed at the cutting edge, with an F1-score of 96.68% and an overall accuracy of 98.20%. This is a substantial advancement over earlier deep-learning models for skin cancer detection, which typically reach accuracies in the 0.90 to 0.95 range."

The number 20 modifies "alternative data augmentation methods." The sentence frames these methods as part of expanding the training dataset. It does not enumerate them. The performance values are quoted as paper claims only; R2C did not measure them. The passage is continuous extracted context; the page was not visually inspected to confirm paragraph breaks.

### Section B: generic definition and symbolic transformations

The extracted text says:

> "Data augmentation is a technique that creates new data from existing data by applying random transformations."

The text then discusses multiple data-augmentation techniques on HAM-10000 and gives a mathematical description summing over 20 different transformations, denoted `T_j`, with `j` ranging from 1 to 20; each `T_j` represents a specific transformation. It does not name those transformations or provide individual probabilities or parameters. It does not explicitly connect the formula to Table 2's `Augmented Images` cells, the 13-technique statement, or the conclusion's 20-method statement.

### Preprocessing terms

Section A is titled `A. DATA PREPROCESSING`. Its continuation describes Gray World and Retinex color balancing, then says: "We first apply spatial filtering to the image, and then we compute the log-ratio to achieve dynamic range compression and contrast augmentation." In this context the phrase concerns image-level contrast enhancement, not an enumerated data-expansion method.

The p. 72857 text, before the `B. DATA AUGMENTATION` heading, says: "We also included the crop function to eliminate the needless part of the image. Finally, we set the image size according to our model." It defines a crop function mathematically. This passage is under preprocessing, and the paper does not call it one of the 13 or 20 data-augmentation techniques.

The paper also describes hair removal in preprocessing and names it alongside color balancing in the conclusion. These terms are not individually identified as members of either data-augmentation set.

### Section IV-C source context

Section IV-C states:

> "We first divided the HAM-10000 dataset into training and testing. The testing dataset consisted of 1332 original images."
>
> "To avoid the overfitting problem, we applied data augmentation technique on training dataset to improve the all the classes in the 9-class dataset. After that, we further divided the training dataset into training and validation."
>
> "The training dataset contained 37,883 images that consisted of original and augmentation images."
>
> "Similarly, the validation dataset contained 6,686 images that also consisted of original and augmentation images."

These counts and locators were independently verified in R2A-SV1. The paper does not supply a class-level ledger linking them to Table 2.

## Inventory conclusion

No individual dataset-augmentation operation is named in the passages that count 13 or 20. Section B's 20 transformations are symbolic and unnamed. Crop, image-level contrast enhancement, hair removal, Gray World, and Retinex appear in preprocessing/color-balancing contexts; the paper does not establish that they are members of the 13- or 20-method sets.
